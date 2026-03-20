"""TUI interaction tests using Textual's Pilot API.

These tests exercise the NetBoxTuiApp without a real terminal or NetBox server.
All API calls are intercepted by a mock client, and file-system state I/O is
patched out so the tests are fully hermetic.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from netbox_cli.api import ApiResponse
from netbox_cli.schema import build_schema_index
from netbox_cli.ui.app import FilterModal, NetBoxTuiApp
from netbox_cli.ui.state import TuiState, ViewState
from textual.widgets import DataTable, Input, Static, TabbedContent, Tree


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_OPENAPI_PATH = Path(__file__).parent.parent / "reference" / "openapi" / "netbox-openapi.json"

FAKE_DEVICES = [
    {"id": 1, "name": "switch01", "status": "active", "display": "switch01"},
    {"id": 2, "name": "router01", "status": "planned", "display": "router01"},
]


def _list_response(items: list) -> ApiResponse:
    body = json.dumps({"count": len(items), "results": items, "next": None, "previous": None})
    return ApiResponse(status=200, text=body)


@pytest.fixture()
def real_index():
    return build_schema_index(_OPENAPI_PATH)


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    return client


@pytest.fixture(autouse=True)
def isolate_tui_state():
    """Prevent all tests from reading/writing ~/.config/netbox-cli/tui_state.json."""
    fresh = TuiState(last_view=ViewState())
    with (
        patch("netbox_cli.ui.app.load_tui_state", return_value=fresh),
        patch("netbox_cli.ui.app.save_tui_state"),
    ):
        yield


def _make_app(mock_client, real_index, theme: str = "default") -> NetBoxTuiApp:
    return NetBoxTuiApp(client=mock_client, index=real_index, theme_name=theme)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _first_leaf_with_data(tree: Tree) -> object | None:
    """BFS over tree nodes; return first leaf that carries (group, resource) data."""
    stack = list(tree.root.children)
    while stack:
        node = stack.pop(0)
        if node.data is not None:
            return node
        stack.extend(node.children)
    return None


def _static_text(widget: Static) -> str:
    """Return the text content of a Static widget as a plain string."""
    return str(widget.content).lower()


# ---------------------------------------------------------------------------
# 1. Startup / mount
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_app_mounts_and_nav_tree_is_populated(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#nav_tree", Tree)
        assert tree.root.children, "Navigation tree should have at least one top-level menu"


@pytest.mark.asyncio
async def test_initial_context_line_is_none(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        ctx = app.query_one("#context_line", Static)
        assert "none" in _static_text(ctx)


@pytest.mark.asyncio
async def test_default_theme_name(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        # app.theme_name is our attribute, not Textual's internal theme name
        assert app.theme_name == "default"


@pytest.mark.asyncio
async def test_dracula_theme_name(mock_client, real_index):
    app = _make_app(mock_client, real_index, theme="dracula")
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        assert app.theme_name == "dracula"
        assert app.theme == "dracula"


# ---------------------------------------------------------------------------
# 2. Key bindings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_slash_key_focuses_search_input(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("/")
        await pilot.pause()
        assert app.query_one("#global_search", Input).has_focus


@pytest.mark.asyncio
async def test_g_key_focuses_nav_tree(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        # Move focus to the results DataTable (does not consume `g`)
        await pilot.press("s")
        await pilot.pause()
        assert app.query_one("#results_table", DataTable).has_focus

        # Now `g` should bubble to the App and trigger action_focus_navigation
        await pilot.press("g")
        await pilot.pause()
        assert app.query_one("#nav_tree", Tree).has_focus


@pytest.mark.asyncio
async def test_s_key_focuses_results_table(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("s")
        await pilot.pause()
        assert app.query_one("#results_table", DataTable).has_focus


@pytest.mark.asyncio
async def test_d_key_switches_to_details_tab(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        tabs = app.query_one("#main_tabs", TabbedContent)
        assert tabs.active == "details_tab"


@pytest.mark.asyncio
async def test_q_key_quits_app(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("q")
        # App exits cleanly — run_test context manager completes without error


@pytest.mark.asyncio
async def test_close_button_exits_app(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.click("#close_tui_button")
        await pilot.pause()


# ---------------------------------------------------------------------------
# 3. Navigation tree selection → API load
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_nav_tree_selection_triggers_api_call(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None, "No navigable leaf node found in the tree"

        expected_group, expected_resource = leaf.data
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()  # allow async _load_rows worker to complete

        mock_client.request.assert_called()
        assert app.current_group == expected_group
        assert app.current_resource == expected_resource


@pytest.mark.asyncio
async def test_nav_tree_selection_updates_context_line(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None

        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()

        ctx = app.query_one("#context_line", Static)
        assert "none" not in _static_text(ctx)


@pytest.mark.asyncio
async def test_nav_tree_selection_populates_results_table(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None

        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        assert len(app.current_rows) == len(FAKE_DEVICES)
        table = app.query_one("#results_table", DataTable)
        assert table.row_count == len(FAKE_DEVICES)


@pytest.mark.asyncio
async def test_nav_tree_api_error_shows_status(mock_client, real_index):
    mock_client.request = AsyncMock(side_effect=RuntimeError("connection refused"))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None

        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        status = app.query_one("#results_status", Static)
        assert "failed" in _static_text(status)


# ---------------------------------------------------------------------------
# 4. Row selection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_space_toggles_row_selection(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        assert len(app.current_rows) > 0
        assert len(app.selected_row_ids) == 0

        # Focus table and toggle first row
        app.query_one("#results_table", DataTable).focus()
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert len(app.selected_row_ids) == 1

        # Toggle again to deselect
        await pilot.press("space")
        await pilot.pause()
        assert len(app.selected_row_ids) == 0


@pytest.mark.asyncio
async def test_a_key_selects_all_rows(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        assert len(app.current_rows) > 0

        await pilot.press("a")
        await pilot.pause()
        assert len(app.selected_row_ids) == len(FAKE_DEVICES)


@pytest.mark.asyncio
async def test_a_key_deselects_all_when_all_selected(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        await pilot.press("a")
        await pilot.pause()
        assert len(app.selected_row_ids) == len(FAKE_DEVICES)

        await pilot.press("a")
        await pilot.pause()
        assert len(app.selected_row_ids) == 0


# ---------------------------------------------------------------------------
# 5. Search / filter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_search_input_submit_triggers_reload(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        call_count_after_load = mock_client.request.call_count

        await pilot.press("/")
        await pilot.pause()
        app.query_one("#global_search", Input).value = "switch01"
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()

        assert mock_client.request.call_count > call_count_after_load


@pytest.mark.asyncio
async def test_f_key_opens_filter_modal(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FilterModal)


@pytest.mark.asyncio
async def test_filter_modal_escape_dismisses(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FilterModal)

        await pilot.press("escape")
        await pilot.pause()
        assert not isinstance(app.screen, FilterModal)


@pytest.mark.asyncio
async def test_filter_modal_cancel_button_dismisses(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FilterModal)

        await pilot.click("#cancel")
        await pilot.pause()
        assert not isinstance(app.screen, FilterModal)


@pytest.mark.asyncio
async def test_filter_modal_apply_updates_search_bar(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        await pilot.press("f")
        await pilot.pause()
        assert isinstance(app.screen, FilterModal)

        modal = app.screen
        modal.query_one("#filter_key", Input).value = "name"
        modal.query_one("#filter_value", Input).value = "switch01"

        await pilot.click("#apply")
        await pilot.pause()
        await pilot.pause()

        assert not isinstance(app.screen, FilterModal)
        assert app.query_one("#global_search", Input).value == "name=switch01"


@pytest.mark.asyncio
async def test_filter_modal_apply_empty_key_shows_warning(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50), notifications=True) as pilot:
        await pilot.pause()
        await pilot.press("f")
        await pilot.pause()

        modal = app.screen
        modal.query_one("#filter_key", Input).value = ""
        modal.query_one("#filter_value", Input).value = "switch01"

        await pilot.click("#apply")
        await pilot.pause()

        # Modal stays open when field key is empty
        assert isinstance(app.screen, FilterModal)


# ---------------------------------------------------------------------------
# 6. Refresh action
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_r_key_refreshes_current_resource(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        call_count_after_load = mock_client.request.call_count

        await pilot.press("r")
        await pilot.pause()
        await pilot.pause()

        assert mock_client.request.call_count > call_count_after_load


@pytest.mark.asyncio
async def test_r_key_does_nothing_without_resource(mock_client, real_index):
    """Refresh with no resource selected should not trigger resource list calls."""
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # isolate_tui_state ensures load_tui_state returns a blank ViewState
        assert app.current_group is None
        calls_before = list(mock_client.request.call_args_list)
        await pilot.press("r")
        await pilot.pause()

        # Health probe may call GET "/" in background; assert no additional calls
        # were made by pressing refresh without a selected resource.
        assert mock_client.request.call_args_list == calls_before


# ---------------------------------------------------------------------------
# 7. Pure-unit tests for internal helpers (no Pilot needed)
# ---------------------------------------------------------------------------

def test_query_from_search_plain_text():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._query_from_search("switch") == {"q": "switch"}


def test_query_from_search_key_value():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._query_from_search("name=switch01") == {"name": "switch01"}


def test_query_from_search_multi_key_value():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._query_from_search("name=switch01,role=leaf") == {"name": "switch01", "role": "leaf"}


def test_query_from_search_empty():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._query_from_search("") == {}


def test_row_identity_uses_id():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"id": 42, "name": "x"}, 0) == "42"


def test_row_identity_fallback_to_index():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"name": "x"}, 7) == "row:7"


def test_row_identity_none_id_fallback():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"id": None, "name": "x"}, 3) == "row:3"
