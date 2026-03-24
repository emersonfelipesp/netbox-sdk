"""TUI interaction tests using Textual's Pilot API.

These tests exercise the NetBoxTuiApp without a real terminal or NetBox server.
All API calls are intercepted by a mock client, and file-system state I/O is
patched out so the tests are fully hermetic.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.color import Color
from textual.coordinate import Coordinate
from textual.widgets import (
    Button,
    DataTable,
    Input,
    ListItem,
    ListView,
    OptionList,
    Select,
    Static,
    TabbedContent,
    Tree,
)

from netbox_cli.api import ApiResponse, ConnectionProbe
from netbox_cli.schema import build_schema_index
from netbox_cli.theme_registry import load_theme_catalog
from netbox_cli.trace_ascii import render_any_trace_ascii, render_cable_trace_ascii
from netbox_cli.ui.app import TOPBAR_CLI_LABEL, NetBoxTuiApp, run_tui
from netbox_cli.ui.chrome import SWITCH_TO_DEV_TUI, SWITCH_TO_MAIN_TUI
from netbox_cli.ui.formatting import configure_semantic_styles, semantic_cell
from netbox_cli.ui.navigation import build_navigation_menus
from netbox_cli.ui.state import TuiState, ViewState
from netbox_cli.ui.widgets import SPONSOR_URL, ContextBreadcrumb
from tests.conftest import OPENAPI_PATH

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

FAKE_DEVICES = [
    {"id": 1, "name": "switch01", "status": "active", "display": "switch01"},
    {"id": 2, "name": "router01", "status": "planned", "display": "router01"},
]

FAKE_DEVICE_DETAIL = {
    "id": 1,
    "name": "switch01",
    "display": "switch01",
    "status": "active",
    "device_type": {
        "id": 10,
        "name": "MA5800",
        "display": "MA5800",
        "url": "/api/dcim/device-types/10/",
        "display_url": "/dcim/device-types/10/",
    },
}

FAKE_DEVICE_TYPE_DETAIL = {
    "id": 10,
    "name": "MA5800",
    "display": "MA5800",
    "manufacturer": {
        "id": 88,
        "name": "Huawei",
        "display": "Huawei",
        "url": "/api/dcim/manufacturers/88/",
        "display_url": "/dcim/manufacturers/88/",
    },
}

FAKE_INTERFACE_ROW = {
    "id": 4,
    "name": "GigabitEthernet0/1/1",
    "display": "GigabitEthernet0/1/1",
    "status": "active",
    "cable": {"id": 36, "display": "#36"},
}

FAKE_INTERFACE_DETAIL = {
    "id": 4,
    "name": "GigabitEthernet0/1/1",
    "display": "GigabitEthernet0/1/1",
    "status": "active",
    "device": {
        "id": 1,
        "display": "dmi01-akron-rtr01",
        "name": "dmi01-akron-rtr01",
    },
    "cable": {"id": 36, "display": "#36"},
}

FAKE_INTERFACE_TRACE = [
    [
        [
            {
                "id": 4,
                "display": "GigabitEthernet0/1/1",
                "name": "GigabitEthernet0/1/1",
                "device": {
                    "id": 1,
                    "display": "dmi01-akron-rtr01",
                    "name": "dmi01-akron-rtr01",
                },
            }
        ],
        {"id": 36, "display": "Cable #36", "status": "connected"},
        [
            {
                "id": 171,
                "display": "GigabitEthernet1/0/2",
                "name": "GigabitEthernet1/0/2",
                "device": {
                    "id": 14,
                    "display": "dmi01-akron-sw01",
                    "name": "dmi01-akron-sw01",
                },
            }
        ],
    ]
]

FAKE_CABLE_ROW = {
    "id": 4,
    "display": "#4",
    "label": "",
    "status": "connected",
}

FAKE_CABLE_DETAIL = {
    "id": 4,
    "display": "#4",
    "label": "",
    "status": "connected",
    "type": "smf",
}

FAKE_CIRCUIT_TERMINATION_ROW = {
    "id": 15,
    "display": "DEOW4921: Termination Z",
    "cable": {"id": 1, "display": "HQ1"},
    "term_side": "Z",
}

FAKE_CIRCUIT_TERMINATION_DETAIL = {
    "id": 15,
    "display": "DEOW4921: Termination Z",
    "cable": {"id": 1, "display": "HQ1"},
    "term_side": "Z",
    "circuit": {
        "id": 14,
        "display": "DEOW4921",
        "cid": "DEOW4921",
        "provider": {"id": 5, "display": "Level 3", "name": "Level 3"},
    },
}

FAKE_CIRCUIT_TERMINATION_PATHS = [
    {
        "id": 160,
        "path": [
            [
                {
                    "id": 157,
                    "url": "https://demo.netbox.dev/api/dcim/interfaces/157/",
                    "display": "GigabitEthernet0/0/0",
                    "name": "GigabitEthernet0/0/0",
                    "device": {
                        "id": 13,
                        "display": "dmi01-yonkers-rtr01",
                        "name": "dmi01-yonkers-rtr01",
                    },
                }
            ],
            [
                {
                    "id": 1,
                    "url": "https://demo.netbox.dev/api/dcim/cables/1/",
                    "display": "HQ1",
                    "label": "HQ1",
                }
            ],
            [
                {
                    "id": 15,
                    "url": "https://demo.netbox.dev/api/circuits/circuit-terminations/15/",
                    "display": "DEOW4921: Termination Z",
                    "circuit": {
                        "id": 14,
                        "display": "DEOW4921",
                        "cid": "DEOW4921",
                        "provider": {
                            "id": 5,
                            "display": "Level 3",
                            "name": "Level 3",
                        },
                    },
                }
            ],
            [
                {
                    "id": 42,
                    "url": "https://demo.netbox.dev/api/circuits/circuit-terminations/42/",
                    "display": "DEOW4921: Termination A",
                    "circuit": {
                        "id": 14,
                        "display": "DEOW4921",
                        "cid": "DEOW4921",
                        "provider": {
                            "id": 5,
                            "display": "Level 3",
                            "name": "Level 3",
                        },
                    },
                }
            ],
            [
                {
                    "id": 1,
                    "url": "https://demo.netbox.dev/api/circuits/provider-networks/1/",
                    "display": "Level3 MPLS",
                    "name": "Level3 MPLS",
                }
            ],
        ],
        "is_active": True,
        "is_complete": True,
        "is_split": False,
    }
]


def _list_response(items: list) -> ApiResponse:
    body = json.dumps({"count": len(items), "results": items, "next": None, "previous": None})
    return ApiResponse(status=200, text=body)


def _detail_response(payload: dict) -> ApiResponse:
    return ApiResponse(status=200, text=json.dumps(payload))


def _assert_color_close(actual: Color, expected: Color, tolerance: int = 1) -> None:
    assert abs(actual.r - expected.r) <= tolerance
    assert abs(actual.g - expected.g) <= tolerance
    assert abs(actual.b - expected.b) <= tolerance
    assert abs(int(actual.a * 255) - int(expected.a * 255)) <= tolerance


@pytest.mark.asyncio
async def test_main_tui_support_modal_opens_sponsors_page(mock_client) -> None:
    app = NetBoxTuiApp(client=mock_client, index=build_schema_index(OPENAPI_PATH))
    app.open_url = MagicMock()

    async with app.run_test() as pilot:
        await pilot.pause()
        app.on_support_pressed()
        await pilot.pause()
        getattr(app.screen, "open_sponsor_page")()

        app.open_url.assert_called_once_with(SPONSOR_URL)
        app.exit()


@pytest.mark.asyncio
async def test_main_tui_support_modal_copy_button_copies_url(mock_client) -> None:
    app = NetBoxTuiApp(client=mock_client, index=build_schema_index(OPENAPI_PATH))
    app.copy_to_clipboard = MagicMock()

    async with app.run_test() as pilot:
        await pilot.pause()
        app.on_support_pressed()
        await pilot.pause()
        await pilot.click("#support_modal_copy_url")
        await pilot.pause()

        app.copy_to_clipboard.assert_called_once_with(SPONSOR_URL)
        app.exit()


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ["dracula", "netbox-light", "netbox-dark"])
async def test_main_tui_support_modal_surfaces_follow_theme(mock_client, theme_name) -> None:
    app = NetBoxTuiApp(
        client=mock_client,
        index=build_schema_index(OPENAPI_PATH),
        theme_name=theme_name,
    )

    async with app.run_test() as pilot:
        await pilot.pause()
        app.on_support_pressed()
        await pilot.pause()

        theme = app.theme_catalog.theme_for(theme_name)
        modal = app.screen_stack[-1]
        dialog = modal.query_one("#support_modal_dialog", object)
        title = modal.query_one("#support_modal_title", object)
        copy = modal.query_one("#support_modal_copy", object)
        copy_url_button = modal.query_one("#support_modal_copy_url", object)
        url = modal.query_one("#support_modal_url", object)
        open_button = modal.query_one("#support_modal_open", object)
        close_button = modal.query_one("#support_modal_close", object)

        assert dialog.styles.background == Color.parse(theme.colors["surface"])
        assert title.styles.color == Color.parse(theme.colors["primary"])
        assert "⭐" in str(title.content)
        assert "⭐" in str(copy.content)
        assert url.styles.color == Color.parse(theme.variables["nb-muted-text"])
        assert copy_url_button.styles.color == Color.parse(theme.variables["nb-muted-text"])
        assert open_button.styles.background == Color.parse(theme.colors["panel"])
        assert open_button.styles.color == Color.parse(theme.colors["primary"])
        assert close_button.styles.background == Color.parse("transparent")
        open_button.focus()
        await pilot.pause()
        assert open_button.styles.background == Color.parse(theme.colors["panel"])
        assert open_button.styles.background_tint == Color.parse("transparent")
        assert close_button.styles.color == Color.parse(theme.variables["nb-muted-text"])
        app.exit()


@pytest.mark.asyncio
async def test_main_tui_support_modal_uses_selected_theme_after_runtime_switch(
    mock_client, real_index
) -> None:
    app = _make_app(mock_client, real_index, theme="netbox-dark")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        app.query_one("#theme_select", Select).value = "dracula"
        await pilot.pause()
        await pilot.pause()
        app.on_support_pressed()
        await pilot.pause()

        theme = app.theme_catalog.theme_for("dracula")
        modal = app.screen_stack[-1]
        dialog = modal.query_one("#support_modal_dialog", object)
        title = modal.query_one("#support_modal_title", object)

        assert dialog.styles.background == Color.parse(theme.colors["surface"])
        assert title.styles.color == Color.parse(theme.colors["primary"])


@pytest.fixture()
def real_index():
    return build_schema_index(OPENAPI_PATH)


_PROBE_OK = ConnectionProbe(status=200, version="4.2", ok=True, error=None)


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    # Short-circuit _probe_connection_health so it never calls client.request
    client.probe_connection = AsyncMock(return_value=_PROBE_OK)
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


def _make_app(mock_client, real_index, theme: str = "netbox-dark") -> NetBoxTuiApp:
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


def test_tui_view_selector_requests_dev_mode(mock_client, real_index) -> None:
    app = _make_app(mock_client, real_index)
    app.exit = MagicMock()

    app.on_view_changed(MagicMock(value="dev"))

    app.exit.assert_called_once_with(result=SWITCH_TO_DEV_TUI)


def test_run_tui_can_switch_into_dev_mode(mock_client, real_index) -> None:
    launches: list[tuple[str, str | None, bool | None]] = []

    class FakeMainApp:
        def __init__(self, *, client, index, theme_name, demo_mode):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("main", theme_name, demo_mode))

        def run(self):
            return SWITCH_TO_DEV_TUI

    class FakeDevApp:
        def __init__(self, *, client, index, theme_name):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("dev", theme_name, None))

        def run(self):
            return None

    with (
        patch("netbox_cli.ui.app.NetBoxTuiApp", FakeMainApp),
        patch("netbox_cli.ui.dev_app.NetBoxDevTuiApp", FakeDevApp),
    ):
        run_tui(client=mock_client, index=real_index, theme_name="dracula", demo_mode=False)

    assert launches == [
        ("main", "dracula", False),
        ("dev", "dracula", None),
    ]


def test_run_tui_can_switch_back_from_dev_in_demo_mode(mock_client, real_index) -> None:
    launches: list[tuple[str, str | None, bool | None]] = []
    dev_runs = 0

    class FakeMainApp:
        def __init__(self, *, client, index, theme_name, demo_mode):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("main", theme_name, demo_mode))

        def run(self):
            return (
                None
                if len([item for item in launches if item[0] == "main"]) > 1
                else SWITCH_TO_DEV_TUI
            )

    class FakeDevApp:
        def __init__(self, *, client, index, theme_name):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("dev", theme_name, None))

        def run(self):
            nonlocal dev_runs
            dev_runs += 1
            return SWITCH_TO_MAIN_TUI if dev_runs == 1 else None

    with (
        patch("netbox_cli.ui.app.NetBoxTuiApp", FakeMainApp),
        patch("netbox_cli.ui.dev_app.NetBoxDevTuiApp", FakeDevApp),
    ):
        run_tui(client=mock_client, index=real_index, theme_name="dracula", demo_mode=True)

    assert launches == [
        ("main", "dracula", True),
        ("dev", "dracula", None),
        ("main", "dracula", True),
    ]


def test_run_tui_preserves_runtime_changed_theme_across_view_switch(
    mock_client, real_index
) -> None:
    launches: list[tuple[str, str | None, bool | None]] = []

    class FakeMainApp:
        def __init__(self, *, client, index, theme_name, demo_mode):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("main", theme_name, demo_mode))

        def run(self):
            self.theme_name = "dracula"
            return SWITCH_TO_DEV_TUI

    class FakeDevApp:
        def __init__(self, *, client, index, theme_name):  # noqa: ANN001
            self.theme_name = theme_name
            launches.append(("dev", theme_name, None))

        def run(self):
            return None

    with (
        patch("netbox_cli.ui.app.NetBoxTuiApp", FakeMainApp),
        patch("netbox_cli.ui.dev_app.NetBoxDevTuiApp", FakeDevApp),
    ):
        run_tui(client=mock_client, index=real_index, theme_name="netbox-dark", demo_mode=False)

    assert launches == [
        ("main", "netbox-dark", False),
        ("dev", "dracula", None),
    ]


def _leaf_for_resource(tree: Tree, group: str, resource: str) -> object | None:
    """Return the leaf node matching a specific (group, resource) pair."""
    stack = list(tree.root.children)
    while stack:
        node = stack.pop(0)
        if node.data == (group, resource):
            return node
        stack.extend(node.children)
    return None


def _static_text(widget: Static) -> str:
    """Return the text content of a Static widget as a plain string."""
    return str(widget.content).lower()


def _breadcrumb_text(widget: ContextBreadcrumb) -> str:
    """Return the combined text of all Static children inside a ContextBreadcrumb."""
    return " ".join(str(s.content).lower() for s in widget.query(Static))


def _truecolor_hex(color: object) -> str:
    """Return a normalized #rrggbb hex string for a Textual/Rich color."""
    if hasattr(color, "get_truecolor"):
        return color.get_truecolor().hex.lower()
    return getattr(color, "hex").lower()


def test_unhandled_tui_exception_uses_user_message(mock_client, real_index) -> None:
    app = _make_app(mock_client, real_index)
    captured: list[object] = []

    def _panic(*renderables: object) -> None:
        captured.extend(renderables)

    app.panic = _panic  # type: ignore[method-assign]
    app._handle_exception(RuntimeError("boom"))

    assert app._return_code == 1
    assert app._exception is not None
    assert captured
    message = str(captured[0])
    assert "Application error" in message
    assert "boom" in message
    assert "Traceback" not in message


# ---------------------------------------------------------------------------
# 1. Startup / mount
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_app_mounts_and_nav_tree_is_populated(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#nav_tree", Tree)
        expected_labels = [menu.label for menu in build_navigation_menus(real_index)]
        actual_labels = [node.label.plain for node in tree.root.children]
        assert actual_labels == expected_labels
        assert all(node.children for node in tree.root.children)
        assert all(not node.is_expanded for node in tree.root.children)


@pytest.mark.asyncio
async def test_nav_tree_parent_selection_preserves_auto_expand_state(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        tree = app.query_one("#nav_tree", Tree)
        first_menu = tree.root.children[0]

        assert tree.auto_expand is True
        assert not first_menu.is_expanded
        app.on_nav_selected(Tree.NodeSelected(first_menu).set_sender(tree))
        assert not first_menu.is_expanded

        first_menu.expand()
        app.on_nav_selected(Tree.NodeSelected(first_menu).set_sender(tree))
        assert first_menu.is_expanded


@pytest.mark.asyncio
async def test_initial_context_line_is_none(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        ctx = app.query_one("#context_breadcrumb", ContextBreadcrumb)
        assert "none" in _breadcrumb_text(ctx)


@pytest.mark.asyncio
async def test_topbar_uses_standard_min_height(mock_client, real_index) -> None:
    app = _make_app(mock_client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        topbar = app.query_one("#topbar", object)
        theme_current = app.query_one("#theme_select SelectCurrent", object)
        view_current = app.query_one("#view_select SelectCurrent", object)
        close_button = app.query_one("#close_tui_button", Button)

        assert topbar.styles.min_height.value == 2
        assert theme_current.styles.min_height.value == 2
        assert view_current.styles.min_height.value == 2
        assert close_button.styles.min_height.value == 2


@pytest.mark.asyncio
async def test_default_theme_name(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        # app.theme_name is our attribute, not Textual's internal theme name
        assert app.theme_name == "netbox-dark"


@pytest.mark.asyncio
async def test_dracula_theme_name(mock_client, real_index):
    app = _make_app(mock_client, real_index, theme="dracula")
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        assert app.theme_name == "dracula"
        assert app.theme == "dracula"


@pytest.mark.asyncio
async def test_demo_tui_title_has_themed_demo_suffix(mock_client, real_index):
    app = NetBoxTuiApp(client=mock_client, index=real_index, theme_name="dracula", demo_mode=True)
    expected_suffix = Color.parse(app.theme_catalog.theme_for("dracula").colors["secondary"])

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        suffix = app.query_one("#app_title_demo", Static)
        assert str(suffix.content) == "(Demo Version)"
        assert suffix.styles.color == expected_suffix


@pytest.mark.asyncio
async def test_demo_tui_suffix_aligns_with_topbar_controls(mock_client, real_index) -> None:
    app = NetBoxTuiApp(client=mock_client, index=real_index, theme_name="dracula", demo_mode=True)

    async with app.run_test(size=(160, 20)) as pilot:
        await pilot.pause()

        suffix = app.query_one("#app_title_demo", Static)
        theme_select = app.query_one("#theme_select", object)
        view_select = app.query_one("#view_select", object)

        assert suffix.outer_size.height == 3
        assert suffix.region.y == theme_select.region.y == view_select.region.y


@pytest.mark.asyncio
async def test_topbar_wordmark_renders_centered(mock_client, real_index):
    app = _make_app(mock_client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        topbar = app.query_one("#topbar", object)
        logo = app.query_one("#topbar_logo", Static)
        center_bar = app.query_one("#topbar_center", object)
        center_mid = center_bar.region.x + center_bar.region.width / 2
        topbar_center = topbar.region.x + (topbar.region.width / 2)

        assert "netbox" in _static_text(logo)
        assert str(app.query_one("#topbar_cli_suffix", Static).content) == TOPBAR_CLI_LABEL
        assert abs(center_mid - topbar_center) <= 1.5


@pytest.mark.asyncio
async def test_support_button_aligns_with_other_topbar_controls(mock_client, real_index) -> None:
    app = _make_app(mock_client, real_index, theme="netbox-dark")

    async with app.run_test(size=(160, 20)) as pilot:
        await pilot.pause()

        support = app.query_one("#support_button", object)
        close = app.query_one("#close_tui_button", object)

        assert support.outer_size.height == close.outer_size.height == 3
        assert support.region.y == close.region.y


@pytest.mark.asyncio
async def test_context_breadcrumb_link_matches_plain_text_style(mock_client, real_index) -> None:
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index, theme="netbox-dark")

    async with app.run_test(size=(180, 20)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _leaf_for_resource(tree, "circuits", "circuit-types")
        assert leaf is not None

        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        breadcrumb = app.query_one("#context_breadcrumb", ContextBreadcrumb)
        current = app.query_one(".breadcrumb-current", object)
        link = app.query_one(".breadcrumb-link", object)

        assert breadcrumb.outer_size.height == 3
        assert breadcrumb.region.y == current.region.y == link.region.y
        assert link.styles.color == current.styles.color
        assert str(link.styles.text_style) == str(current.styles.text_style) == "none"


@pytest.mark.asyncio
async def test_plugin_breadcrumb_root_opens_descendant_dropdown(mock_client, real_index) -> None:
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    with patch(
        "netbox_cli.ui.app.discover_plugin_resource_paths",
        AsyncMock(
            return_value=[
                ("/api/plugins/gpon/boards/", "/api/plugins/gpon/boards/{id}/"),
                ("/api/plugins/gpon/line-profiles/", "/api/plugins/gpon/line-profiles/{id}/"),
            ]
        ),
    ):
        app = _make_app(mock_client, real_index, theme="netbox-dark")

        async with app.run_test(size=(180, 24)) as pilot:
            await pilot.pause()
            await pilot.pause()

            tree = app.query_one("#nav_tree", Tree)
            leaf = _leaf_for_resource(tree, "plugins", "gpon/boards")
            assert leaf is not None

            tree.post_message(Tree.NodeSelected(leaf))
            await pilot.pause()
            await pilot.pause()

            plugins_button = next(
                button for button in app.query(".breadcrumb-link") if str(button.label) == "Plugins"
            )
            plugins_button.press()
            await pilot.pause()

            option_list = app.query_one("#context_breadcrumb_menu", OptionList)
            prompts = [
                str(option_list.get_option_at_index(i).prompt)
                for i in range(option_list.option_count)
            ]

            assert "hidden" not in option_list.classes
            assert prompts == ["Gpon"]


@pytest.mark.asyncio
async def test_plugin_group_breadcrumb_dropdown_navigates_to_selected_resource(
    mock_client, real_index
) -> None:
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    with patch(
        "netbox_cli.ui.app.discover_plugin_resource_paths",
        AsyncMock(
            return_value=[
                ("/api/plugins/gpon/boards/", "/api/plugins/gpon/boards/{id}/"),
                ("/api/plugins/gpon/line-profiles/", "/api/plugins/gpon/line-profiles/{id}/"),
            ]
        ),
    ):
        app = _make_app(mock_client, real_index, theme="netbox-dark")

        async with app.run_test(size=(180, 24)) as pilot:
            await pilot.pause()
            await pilot.pause()

            tree = app.query_one("#nav_tree", Tree)
            leaf = _leaf_for_resource(tree, "plugins", "gpon/boards")
            assert leaf is not None

            tree.post_message(Tree.NodeSelected(leaf))
            await pilot.pause()
            await pilot.pause()

            gpon_button = next(
                button for button in app.query(".breadcrumb-link") if str(button.label) == "Gpon"
            )
            gpon_button.press()
            await pilot.pause()

            option_list = app.query_one("#context_breadcrumb_menu", OptionList)
            prompts = [
                str(option_list.get_option_at_index(i).prompt)
                for i in range(option_list.option_count)
            ]
            assert "Line Profiles" in prompts

            option_list.highlighted = prompts.index("Line Profiles")
            option_list.action_select()
            await pilot.pause()
            await pilot.pause()

            assert app.current_group == "plugins"
            assert app.current_resource == "gpon/line-profiles"
            assert "line profiles" in _static_text(app.query_one(".breadcrumb-current", Static))


@pytest.mark.asyncio
async def test_demo_tui_hides_bundled_plugin_navigation_when_runtime_discovery_is_empty(
    mock_client, real_index
) -> None:
    app = NetBoxTuiApp(
        client=mock_client, index=real_index, theme_name="netbox-dark", demo_mode=True
    )

    async with app.run_test(size=(180, 24)) as pilot:
        await pilot.pause()
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        root_labels = [node.label.plain for node in tree.root.children]

        assert "Plugins" not in root_labels
        assert _leaf_for_resource(tree, "plugins", "gpon/boards") is None


@pytest.mark.asyncio
async def test_demo_tui_does_not_restore_stale_plugin_view_when_runtime_has_no_plugins(
    mock_client, real_index
) -> None:
    stale = TuiState(last_view=ViewState(group="plugins", resource="gpon/boards"))
    with patch("netbox_cli.ui.app.load_tui_state", return_value=stale):
        app = NetBoxTuiApp(
            client=mock_client,
            index=real_index,
            theme_name="netbox-dark",
            demo_mode=True,
        )

    async with app.run_test(size=(180, 24)) as pilot:
        await pilot.pause()
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        assert _leaf_for_resource(tree, "plugins", "gpon/boards") is None
        assert app.current_group is None
        assert app.current_resource is None
        assert "<none>" in _breadcrumb_text(app.query_one("#context_breadcrumb", ContextBreadcrumb))


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_theme_background_applies_to_query_bar_and_select(
    mock_client, real_index, theme_name: str
):
    app = _make_app(mock_client, real_index, theme=theme_name)
    expected_background = Color.parse(app.theme_catalog.theme_for(theme_name).colors["background"])

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        query_bar = app.query_one("#query_bar", object)
        theme_current = app.query_one("#theme_select SelectCurrent", object)
        theme_overlay = app.query_one("#theme_select SelectOverlay", object)

        assert query_bar.styles.background == expected_background
        assert theme_current.styles.background.a == 0
        assert theme_overlay.styles.background == expected_background


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_select_inner_styles_follow_theme(mock_client, real_index, theme_name: str) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        current = app.query_one("#theme_select SelectCurrent", object)
        label = app.query_one("#theme_select SelectCurrent Static#label", Static)
        arrow = app.query_one("#theme_select SelectCurrent .arrow", object)

        assert label.styles.color == current.styles.color
        assert arrow.styles.color == current.styles.color.with_alpha(0.55)


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_global_search_input_inner_styles_follow_theme(
    mock_client, real_index, theme_name: str
) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        search = app.query_one("#global_search", Input)
        placeholder = search.get_component_styles("input--placeholder")
        cursor = search.get_component_styles("input--cursor")
        selection = search.get_component_styles("input--selection")
        suggestion = search.get_component_styles("input--suggestion")

        assert placeholder.color == Color.parse(theme.variables["nb-muted-text"])
        assert suggestion.color == Color.parse(theme.variables["nb-muted-text"])
        assert cursor.background == search.styles.color
        assert cursor.color == Color.parse(theme.colors["background"])
        assert selection.background == Color.parse(theme.colors["primary"]).with_alpha(0.35)
        assert selection.color == search.styles.color


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_filter_picker_option_list_inner_styles_follow_theme(
    mock_client, real_index, theme_name: str
) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        app._refresh_filter_fields("dcim", "devices")
        app._open_filter_picker("name")
        await pilot.pause()

        picker = app.query_one("#filter_picker_list", OptionList)
        highlighted = picker.get_component_styles("option-list--option-highlighted")
        hover = picker.get_component_styles("option-list--option-hover")
        disabled = picker.get_component_styles("option-list--option-disabled")
        separator = picker.get_component_styles("option-list--separator")

        assert picker.styles.background == Color.parse(theme.colors["background"])
        assert picker.styles.color is not None
        assert highlighted.background == Color.parse(theme.colors["panel"])
        assert highlighted.color == picker.styles.color
        assert hover.background == Color.parse(theme.colors["panel"])
        assert disabled.color == Color.parse(theme.variables["nb-muted-text"])
        assert separator.color == Color.parse(theme.variables["nb-border-subtle"])


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_main_tabs_follow_theme_tokens(mock_client, real_index, theme_name: str) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        main_tabs = app.query_one("#main_tabs", object)
        switcher = app.query_one("#main_tabs ContentSwitcher", object)
        tabs = list(app.query("#main_tabs Tab"))
        inactive_tab = next(tab for tab in tabs if "-active" not in tab.classes)

        assert main_tabs.styles.background == Color.parse(theme.colors["background"])
        assert switcher.styles.background == Color.parse(theme.colors["background"])
        assert inactive_tab.styles.color == Color.parse(theme.variables["nb-muted-text"])


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_main_tab_labels_stay_visible_across_themes(
    mock_client, real_index, theme_name: str
) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tabs = app.query_one("#main_tabs", TabbedContent)
        content_tabs = list(app.query("#main_tabs ContentTab"))
        assert [tab.label_text for tab in content_tabs] == ["Results", "Details"]
        assert all(tab.size.height == 1 for tab in content_tabs)

        tabs.active = "details_tab"
        await pilot.pause()

        content_tabs = list(app.query("#main_tabs ContentTab"))
        assert [tab.label_text for tab in content_tabs] == ["Results", "Details"]
        assert all(tab.size.height == 1 for tab in content_tabs)


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_footer_inner_styles_follow_theme(mock_client, real_index, theme_name: str) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        footer = app.query_one("Footer", object)
        footer_key = app.query_one("FooterKey", object)
        key_styles = footer_key.get_component_styles("footer-key--key")
        desc_styles = footer_key.get_component_styles("footer-key--description")

        assert footer.styles.background == Color.parse(theme.colors["background"])
        assert footer_key.styles.color == footer.styles.color
        assert key_styles.background == Color.parse(theme.colors["panel"])
        assert key_styles.color == Color.parse(theme.colors["primary"])
        assert desc_styles.color == footer.styles.color


@pytest.mark.asyncio
async def test_tree_and_detail_cursor_styles_follow_theme(mock_client, real_index):
    app = _make_app(mock_client, real_index, theme="dracula")
    expected_panel = app.theme_catalog.theme_for("dracula").colors["panel"].lower()
    expected_subtle = app.theme_catalog.theme_for("dracula").variables["nb-border-subtle"].lower()

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        results_table = app.query_one("#results_table", DataTable)
        detail_table = app.query_one("#detail_table", DataTable)

        tree_cursor = tree.get_component_rich_style("tree--cursor")
        tree_hover = tree.get_component_rich_style("tree--highlight-line")
        tree_highlight = tree.get_component_rich_style("tree--highlight")
        tree_guides_hover = tree.get_component_rich_style("tree--guides-hover")
        results_header_hover = results_table.get_component_rich_style("datatable--header-hover")
        detail_cursor = detail_table.get_component_rich_style("datatable--cursor")
        detail_hover = detail_table.get_component_rich_style("datatable--hover")
        detail_header_hover = detail_table.get_component_rich_style("datatable--header-hover")

        assert _truecolor_hex(tree_cursor.bgcolor) == expected_panel
        assert _truecolor_hex(tree_hover.bgcolor) == expected_panel
        assert _truecolor_hex(tree_highlight.bgcolor) == expected_panel
        assert _truecolor_hex(tree_guides_hover.color) == expected_subtle
        assert _truecolor_hex(results_header_hover.bgcolor) == expected_panel
        assert _truecolor_hex(detail_cursor.bgcolor) == expected_panel
        assert _truecolor_hex(detail_hover.bgcolor) == expected_panel
        assert _truecolor_hex(detail_header_hover.bgcolor) == expected_panel


@pytest.mark.asyncio
async def test_connection_badge_is_single_dot_and_theme_colored(mock_client, real_index):
    app = _make_app(mock_client, real_index, theme="dracula")
    expected_success = Color.parse(
        app.theme_catalog.theme_for("dracula").variables["nb-success-text"]
    )

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()
        await pilot.pause()

        badge = app.query_one("#connection_badge", Static)
        assert _static_text(badge) == "●"
        assert badge.styles.color == expected_success


def test_semantic_cells_use_neutral_chip_background() -> None:
    catalog = load_theme_catalog()
    theme = catalog.theme_for("dracula")
    configure_semantic_styles(colors=theme.colors, variables=theme.variables)

    assert " on " not in semantic_cell("status", "active").style
    assert " on " not in semantic_cell("role", "Placeholder Role").style
    assert " on " not in semantic_cell("tenant", "Tenant A").style


def test_render_cable_trace_ascii_formats_segment() -> None:
    rendered = render_cable_trace_ascii(FAKE_INTERFACE_TRACE)

    assert rendered is not None
    assert "dmi01-akron-rtr01" in rendered
    assert "GigabitEthernet0/1/1" in rendered
    assert "Cable #36" in rendered
    assert "Connected" in rendered
    assert "dmi01-akron-sw01" in rendered
    assert "Trace Completed - 1 segment(s)" in rendered


def test_render_any_trace_ascii_formats_circuit_termination_path() -> None:
    rendered = render_any_trace_ascii(FAKE_CIRCUIT_TERMINATION_PATHS)

    assert rendered is not None
    assert "dmi01-yonkers-rtr01" in rendered
    assert "GigabitEthernet0/0/0" in rendered
    assert "Cable HQ1" in rendered
    assert "DEOW4921: Termination Z" in rendered
    assert "Circuit DEOW4921" in rendered
    assert "Level3 MPLS" in rendered
    assert "Trace Completed - 1 segment(s)" in rendered


@pytest.mark.asyncio
async def test_detail_link_click_redirects_to_linked_object(real_index):
    client = MagicMock()

    async def _request(method: str, path: str, **kwargs):
        if method != "GET":
            raise AssertionError(f"unexpected method: {method}")
        if path == "/api/dcim/devices/":
            return _list_response([FAKE_DEVICE_DETAIL])
        if path == "/api/dcim/devices/1/":
            return _detail_response(FAKE_DEVICE_DETAIL)
        if path == "/api/dcim/device-types/10/":
            return _detail_response(FAKE_DEVICE_TYPE_DETAIL)
        raise AssertionError(f"unexpected path: {path}")

    client.request = AsyncMock(side_effect=_request)
    client.probe_connection = AsyncMock(return_value=_PROBE_OK)

    app = _make_app(client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = None
        stack = list(tree.root.children)
        while stack:
            node = stack.pop(0)
            if node.data == ("dcim", "devices"):
                leaf = node
                break
            stack.extend(node.children)
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        detail_table = app.query_one("#detail_table", DataTable)
        device_type_row = None
        for _ in range(20):
            for row_index in range(detail_table.row_count):
                field_value = (
                    str(detail_table.get_cell_at(Coordinate(row_index, 0))).strip().lower()
                )
                if field_value == "device type":
                    device_type_row = row_index
                    break
            if device_type_row is not None:
                break
            await pilot.pause()

        assert device_type_row is not None, "Expected Device Type field in details"

        value_coord = Coordinate(device_type_row, 1)
        detail_table.post_message(
            DataTable.CellSelected(
                detail_table,
                detail_table.get_cell_at(value_coord),
                coordinate=value_coord,
                cell_key=detail_table.coordinate_to_cell_key(value_coord),
            )
        )
        await pilot.pause()
        await pilot.pause()

        assert app.current_group == "dcim"
        assert app.current_resource == "device-types"
        ctx = app.query_one("#context_breadcrumb", ContextBreadcrumb)
        assert "device types" in _breadcrumb_text(ctx)
        client.request.assert_any_call("GET", "/api/dcim/device-types/10/")


@pytest.mark.asyncio
async def test_interface_detail_shows_ascii_cable_trace(real_index):
    client = MagicMock()

    async def _request(method: str, path: str, **kwargs):
        if method != "GET":
            raise AssertionError(f"unexpected method: {method}")
        if path == "/api/dcim/interfaces/":
            return _list_response([FAKE_INTERFACE_ROW])
        if path == "/api/dcim/interfaces/4/":
            return _detail_response(FAKE_INTERFACE_DETAIL)
        if path == "/api/dcim/interfaces/4/trace/":
            return ApiResponse(status=200, text=json.dumps(FAKE_INTERFACE_TRACE))
        raise AssertionError(f"unexpected path: {path}")

    client.request = AsyncMock(side_effect=_request)
    client.probe_connection = AsyncMock(return_value=_PROBE_OK)

    app = _make_app(client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = None
        stack = list(tree.root.children)
        while stack:
            node = stack.pop(0)
            if node.data == ("dcim", "interfaces"):
                leaf = node
                break
            stack.extend(node.children)
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        trace = app.query_one("#detail_trace", Static)
        trace_text = str(trace.content)
        assert "dmi01-akron-rtr01" in trace_text
        assert "Cable #36" in trace_text
        assert "Trace Completed - 1 segment(s)" in trace_text


@pytest.mark.asyncio
async def test_cable_detail_shows_ascii_cable_trace(real_index):
    client = MagicMock()

    async def _request(method: str, path: str, **kwargs):
        if method != "GET":
            raise AssertionError(f"unexpected method: {method}")
        if path == "/api/dcim/cables/":
            return _list_response([FAKE_CABLE_ROW])
        if path == "/api/dcim/cables/4/":
            return _detail_response(FAKE_CABLE_DETAIL)
        if path == "/api/dcim/cables/4/trace/":
            return ApiResponse(status=200, text=json.dumps(FAKE_INTERFACE_TRACE))
        raise AssertionError(f"unexpected path: {path}")

    client.request = AsyncMock(side_effect=_request)
    client.probe_connection = AsyncMock(return_value=_PROBE_OK)

    app = _make_app(client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = None
        stack = list(tree.root.children)
        while stack:
            node = stack.pop(0)
            if node.data == ("dcim", "cables"):
                leaf = node
                break
            stack.extend(node.children)
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        trace = app.query_one("#detail_trace", Static)
        trace_text = str(trace.content)
        assert "dmi01-akron-rtr01" in trace_text
        assert "Cable #36" in trace_text
        assert "Trace Completed - 1 segment(s)" in trace_text


@pytest.mark.asyncio
async def test_circuit_termination_detail_shows_ascii_path_trace(real_index):
    client = MagicMock()

    async def _request(method: str, path: str, **kwargs):
        if method != "GET":
            raise AssertionError(f"unexpected method: {method}")
        if path == "/api/circuits/circuit-terminations/":
            return _list_response([FAKE_CIRCUIT_TERMINATION_ROW])
        if path == "/api/circuits/circuit-terminations/15/":
            return _detail_response(FAKE_CIRCUIT_TERMINATION_DETAIL)
        if path == "/api/circuits/circuit-terminations/15/paths/":
            return ApiResponse(status=200, text=json.dumps(FAKE_CIRCUIT_TERMINATION_PATHS))
        raise AssertionError(f"unexpected path: {path}")

    client.request = AsyncMock(side_effect=_request)
    client.probe_connection = AsyncMock(return_value=_PROBE_OK)

    app = _make_app(client, real_index, theme="dracula")

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = None
        stack = list(tree.root.children)
        while stack:
            node = stack.pop(0)
            if node.data == ("circuits", "circuit-terminations"):
                leaf = node
                break
            stack.extend(node.children)
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        trace = app.query_one("#detail_trace", Static)
        trace_text = str(trace.content)
        assert "dmi01-yonkers-rtr01" in trace_text
        assert "Cable HQ1" in trace_text
        assert "DEOW4921: Termination Z" in trace_text
        assert "Level3 MPLS" in trace_text


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

        app.on_nav_selected(Tree.NodeSelected(leaf))
        await pilot.pause()

        ctx = app.query_one("#context_breadcrumb", ContextBreadcrumb)
        assert "none" not in _breadcrumb_text(ctx)


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
async def test_nav_tree_selection_shows_center_loading_overlay(mock_client, real_index):
    async def _slow_request(*args, **kwargs):
        await asyncio.sleep(0.5)  # Longer delay for CI stability
        return _list_response(FAKE_DEVICES)

    mock_client.request = AsyncMock(side_effect=_slow_request)
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None

        app.on_nav_selected(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()  # Extra pause for parallel test stability

        overlay = app.query_one("#results_loading_overlay", object)
        status = app.query_one("#results_status", Static)
        spinner = app.query_one("#results_loading_spinner", Static)

        # Wait for loading overlay to appear (race condition in parallel tests)
        for _ in range(20):
            if "hidden" not in overlay.classes:
                break
            await pilot.pause()

        assert "hidden" not in overlay.classes
        assert "-loading" in status.classes
        assert _static_text(spinner) != ""

        for _ in range(20):
            if "hidden" in overlay.classes:
                break
            await pilot.pause()

        assert "hidden" in overlay.classes
        assert "-loading" not in status.classes


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


@pytest.mark.asyncio
async def test_results_loading_status_uses_theme_primary(mock_client, real_index):
    async def _slow_request(*args, **kwargs):
        await asyncio.sleep(0.5)  # Longer delay for CI stability
        return _list_response(FAKE_DEVICES)

    mock_client.request = AsyncMock(side_effect=_slow_request)
    app = _make_app(mock_client, real_index, theme="dracula")
    expected_primary = Color.parse(app.theme_catalog.theme_for("dracula").colors["primary"])

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        for _ in range(20):  # Increased for parallel test stability
            await pilot.pause()
            status = app.query_one("#results_status", Static)
            if "-loading" in status.classes:
                break

        status = app.query_one("#results_status", Static)
        assert "-loading" in status.classes
        assert status.styles.color == expected_primary


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

        app.action_toggle_select_all()
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

        app.action_toggle_select_all()
        await pilot.pause()
        assert len(app.selected_row_ids) == len(FAKE_DEVICES)

        app.action_toggle_select_all()
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
async def test_f_key_opens_filter_overlay(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()
        assert "hidden" not in app.query_one("#filter_picker_overlay", object).classes
        assert app.query_one("#filter_picker_search", Input).has_focus


@pytest.mark.asyncio
async def test_filter_overlay_escape_dismisses(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()
        assert "hidden" not in app.query_one("#filter_picker_overlay", object).classes

        await pilot.press("escape")
        await pilot.pause()
        assert "hidden" in app.query_one("#filter_picker_overlay", object).classes


@pytest.mark.asyncio
async def test_filter_overlay_cancel_button_dismisses(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _first_leaf_with_data(tree)
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()
        assert "hidden" not in app.query_one("#filter_picker_overlay", object).classes

        app.query_one("#filter_picker_cancel", Button).press()
        await pilot.pause()
        assert "hidden" in app.query_one("#filter_picker_overlay", object).classes


@pytest.mark.asyncio
async def test_filter_overlay_apply_updates_search_bar(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _leaf_for_resource(tree, "dcim", "devices")
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()
        app._open_filter_overlay("id")
        await pilot.pause()

        app.query_one("#filter_value", Input).value = "switch01"
        app._apply_filter_overlay()
        await pilot.pause()
        await pilot.pause()

        assert "hidden" in app.query_one("#filter_overlay", object).classes
        assert app.query_one("#global_search", Input).value == "id=switch01"
        assert "ID=switch01" in str(app.query_one("#active_filters", Static).render())


@pytest.mark.asyncio
async def test_filter_select_opens_overlay_for_selected_field(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _leaf_for_resource(tree, "dcim", "devices")
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.query_one("#filter_select", Button).press()
        await pilot.pause()

        assert "hidden" not in app.query_one("#filter_picker_overlay", object).classes
        assert app.query_one("#filter_picker_search", Input).has_focus


@pytest.mark.asyncio
async def test_filter_picker_search_filters_available_fields(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _leaf_for_resource(tree, "dcim", "devices")
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()

        search = app.query_one("#filter_picker_search", Input)
        search.value = "stat"
        app._refresh_filter_picker_list()
        await pilot.pause()

        assert app._visible_filter_fields
        assert all("stat" in label.lower() for label, _ in app._visible_filter_fields)


@pytest.mark.asyncio
async def test_filter_picker_selection_opens_value_overlay(mock_client, real_index):
    mock_client.request = AsyncMock(return_value=_list_response(FAKE_DEVICES))
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        tree = app.query_one("#nav_tree", Tree)
        leaf = _leaf_for_resource(tree, "dcim", "devices")
        assert leaf is not None
        tree.post_message(Tree.NodeSelected(leaf))
        await pilot.pause()
        await pilot.pause()

        app.action_filter_modal()
        await pilot.pause()

        picker = app.query_one("#filter_picker_list", OptionList)
        index = next(
            i for i, (_, value) in enumerate(app._visible_filter_fields) if value == "status"
        )
        picker.focus()
        picker.highlighted = index
        await pilot.press("enter")
        await pilot.pause()

        assert "hidden" in app.query_one("#filter_picker_overlay", object).classes
        assert "hidden" not in app.query_one("#filter_overlay", object).classes
        assert str(app.query_one("#filter_field_label", Static).render()) == "Field: Status"


@pytest.mark.asyncio
async def test_filter_overlay_without_field_shows_warning(mock_client, real_index):
    app = _make_app(mock_client, real_index)
    async with app.run_test(size=(160, 50), notifications=True) as pilot:
        await pilot.pause()
        app._filter_overlay_field = ""
        app.query_one("#filter_overlay", object).remove_class("hidden")
        app.query_one("#filter_value", Input).value = "switch01"
        await pilot.click("#filter_apply")
        await pilot.pause()

        assert "hidden" not in app.query_one("#filter_overlay", object).classes


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("theme_name", "severity", "expected_title_token"),
    (
        ("dracula", "information", "primary"),
        ("dracula", "warning", "warning"),
        ("dracula", "error", "error"),
        ("netbox-dark", "information", "primary"),
        ("netbox-dark", "warning", "warning"),
        ("netbox-dark", "error", "error"),
        ("netbox-light", "information", "primary"),
        ("netbox-light", "warning", "warning"),
        ("netbox-light", "error", "error"),
    ),
)
async def test_notifications_toasts_follow_theme_tokens(
    mock_client, real_index, theme_name: str, severity: str, expected_title_token: str
) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50), notifications=True) as pilot:
        await pilot.pause()
        app.notify("Theme-driven toast body", title="Heads up", severity=severity)
        await pilot.pause()

        rack = app.query_one("ToastRack", object)
        holder = app.query_one("ToastHolder", object)
        toast = app.query_one("Toast", object)
        title = toast.get_component_styles("toast--title")

        assert rack.styles.background.a == 0
        assert holder.styles.background.a == 0
        assert toast.styles.background == Color.parse(theme.colors["panel"])
        _assert_color_close(title.color, Color.parse(theme.colors[expected_title_token]))


@pytest.mark.asyncio
@pytest.mark.parametrize("theme_name", ("dracula", "netbox-dark", "netbox-light"))
async def test_list_view_item_states_follow_theme(mock_client, real_index, theme_name: str) -> None:
    app = _make_app(mock_client, real_index, theme=theme_name)
    theme = app.theme_catalog.theme_for(theme_name)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        list_view = ListView(
            ListItem(Static("Alpha"), id="theme_probe_item_a"),
            ListItem(Static("Beta"), id="theme_probe_item_b"),
            id="theme_probe_list",
        )
        await app.query_one("#main", object).mount(list_view)
        await pilot.pause()

        item_a = app.query_one("#theme_probe_item_a", ListItem)
        item_b = app.query_one("#theme_probe_item_b", ListItem)
        item_a.add_class("-highlight")
        item_b.add_class("-hovered")
        list_view.focus()
        await pilot.pause()

        assert list_view.styles.background == Color.parse(theme.colors["surface"])
        assert item_a.styles.background == Color.parse(theme.colors["panel"])
        assert item_a.styles.color == list_view.styles.color
        assert item_b.styles.background == Color.parse(theme.colors["panel"])
        assert item_b.styles.color == list_view.styles.color


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

        app.action_refresh()
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
    app.current_group = "dcim"
    app.current_resource = "devices"
    app.index = build_schema_index(OPENAPI_PATH)
    assert app._query_from_search("name=switch01") == {"name__ic": "switch01"}


def test_query_from_search_multi_key_value():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    app.current_group = "dcim"
    app.current_resource = "devices"
    app.index = build_schema_index(OPENAPI_PATH)
    assert app._query_from_search("name=switch01,role=leaf") == {
        "name__ic": "switch01",
        "role": "leaf",
    }


def test_query_from_search_empty():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._query_from_search("") == {}


def test_query_from_search_status_stays_exact():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    app.current_group = "dcim"
    app.current_resource = "devices"
    app.index = build_schema_index(OPENAPI_PATH)
    assert app._query_from_search("status=active") == {"status": "active"}


def test_row_identity_uses_id():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"id": 42, "name": "x"}, 0) == "42"


def test_row_identity_fallback_to_index():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"name": "x"}, 7) == "row:7"


def test_row_identity_none_id_fallback():
    app = NetBoxTuiApp.__new__(NetBoxTuiApp)
    assert app._row_identity({"id": None, "name": "x"}, 3) == "row:3"
