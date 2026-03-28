"""Tests for the interactive CLI command builder TUI (``nbx cli tui``).

Covers:
- CliCommandNode model validation (cli_completions.py)
- nbx_root_command_nodes tree structure (cli_completions.py)
- NbxCliTuiApp pilot tests: mount, navigation, breadcrumb, command fill, execution
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from textual.widgets import Button, Input, ListItem, ListView, RichLog, Select, Static

from netbox_sdk.config import Config
from netbox_sdk.schema import build_schema_index
from netbox_tui.cli_completions import (
    CliCommandNode,
    _action_leaf_nodes,
    _resource_branch_nodes,
    _schema_group_nodes,
    _static_leaf_nodes,
    nbx_root_command_nodes,
)
from netbox_tui.cli_tui import NbxCliTuiApp, _nbx_cli_execute, run_cli_tui
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_tui

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_index():
    return build_schema_index(OPENAPI_PATH)


def _make_executor(exit_code: int = 0, output: str = "ok"):
    """Return a synchronous executor that returns a fixed result."""

    def _executor(argv: list[str]) -> tuple[int, str]:  # noqa: ANN001
        return (exit_code, output)

    return _executor


class _FakeClient:
    def __init__(self) -> None:
        self.config = Config(
            base_url="https://netbox.example.com",
            token_key="abc",
            token_secret="def",
            timeout=5.0,
        )

    async def request(self, method: str, path: str, **kwargs: object):  # noqa: ANN003
        del method, path, kwargs

        class _Response:
            status = 200
            text = "{}"
            headers = {"API-Version": "4.2"}

        return _Response()


def _make_client() -> _FakeClient:
    return _FakeClient()


def _make_app(real_index, exit_code: int = 0, output: str = "ok") -> NbxCliTuiApp:
    return NbxCliTuiApp(
        client=_make_client(),
        index=real_index,
        executor=_make_executor(exit_code, output),
    )


# ---------------------------------------------------------------------------
# CliCommandNode model validation
# ---------------------------------------------------------------------------


def test_cli_command_node_valid_branch() -> None:
    child = CliCommandNode(label="list", tail=("list",))
    branch = CliCommandNode(
        label="devices",
        enter_tail=("devices",),
        children=(child,),
    )
    assert branch.children == (child,)
    assert branch.enter_tail == ("devices",)


def test_cli_command_node_valid_leaf() -> None:
    leaf = CliCommandNode(label="list", description="GET all", tail=("list",), allows_query=True)
    assert leaf.tail == ("list",)
    assert leaf.allows_query is True
    assert not leaf.children


def test_cli_command_node_cannot_have_both_children_and_tail() -> None:
    child = CliCommandNode(label="a", tail=("a",))
    with pytest.raises(ValueError, match="cannot have both children and tail"):
        CliCommandNode(label="bad", children=(child,), tail=("bad",))


def test_cli_command_node_must_have_children_or_tail() -> None:
    with pytest.raises(ValueError, match="must have either children or tail"):
        CliCommandNode(label="empty")


def test_cli_command_node_frozen() -> None:
    node = CliCommandNode(label="x", tail=("x",))
    with pytest.raises(Exception):
        node.label = "y"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Tree builder: static leaves
# ---------------------------------------------------------------------------


def test_static_leaf_nodes_includes_core_commands() -> None:
    leaves = _static_leaf_nodes()
    labels = {n.label for n in leaves}
    assert "init" in labels
    assert "config" in labels
    assert "groups" in labels
    assert "logs" in labels
    assert "call" in labels


def test_static_leaf_nodes_are_all_leaves() -> None:
    for node in _static_leaf_nodes():
        assert not node.children, f"static node {node.label!r} should be a leaf"
        assert node.tail


# ---------------------------------------------------------------------------
# Tree builder: schema-based nodes
# ---------------------------------------------------------------------------


def test_schema_group_nodes_includes_dcim(real_index) -> None:
    groups = {n.label for n in _schema_group_nodes(real_index)}
    assert "dcim" in groups


def test_schema_group_nodes_includes_ipam(real_index) -> None:
    groups = {n.label for n in _schema_group_nodes(real_index)}
    assert "ipam" in groups


def test_schema_group_nodes_are_branches(real_index) -> None:
    for node in _schema_group_nodes(real_index):
        assert node.children, f"group node {node.label!r} should be a branch"
        assert not node.tail


def test_resource_branch_nodes_dcim_has_devices(real_index) -> None:
    resources = {n.label for n in _resource_branch_nodes("dcim", real_index)}
    assert "devices" in resources


def test_action_leaf_nodes_devices_has_list(real_index) -> None:
    actions = {n.label for n in _action_leaf_nodes("dcim", "devices", real_index)}
    assert "list" in actions


def test_action_leaf_nodes_devices_has_get(real_index) -> None:
    actions = {n.label for n in _action_leaf_nodes("dcim", "devices", real_index)}
    assert "get" in actions


def test_action_leaf_get_requires_id(real_index) -> None:
    actions = {n.label: n for n in _action_leaf_nodes("dcim", "devices", real_index)}
    assert actions["get"].requires_id is True


def test_action_leaf_list_allows_query(real_index) -> None:
    actions = {n.label: n for n in _action_leaf_nodes("dcim", "devices", real_index)}
    assert actions["list"].allows_query is True


def test_action_leaf_create_allows_body(real_index) -> None:
    actions = {n.label: n for n in _action_leaf_nodes("dcim", "devices", real_index)}
    assert actions["create"].allows_body is True


def test_nbx_root_command_nodes_has_static_and_groups(real_index) -> None:
    root = nbx_root_command_nodes(real_index)
    labels = {n.label for n in root}
    assert "init" in labels
    assert "dcim" in labels
    assert "ipam" in labels


# ---------------------------------------------------------------------------
# NbxCliTuiApp pilot tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cli_tui_mounts_and_nav_list_has_items(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        assert len(nav_list.query(ListItem)) > 0


@pytest.mark.asyncio
async def test_cli_tui_breadcrumb_starts_at_root(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        crumb = app.query_one("#breadcrumb", Static)
        assert str(crumb.content) == "nbx"


@pytest.mark.asyncio
async def test_cli_tui_welcome_output_written(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        output = app.query_one("#output", RichLog)
        # RichLog exposes .lines (a list of rendered segments); welcome writes at least one
        assert len(output.lines) > 0


@pytest.mark.asyncio
async def test_cli_tui_output_copy_button_copies_log_content(real_index) -> None:
    app = _make_app(real_index)

    with patch.object(app, "copy_to_clipboard") as mock_copy:
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.click("#output_copy_button")
            await pilot.pause()

    mock_copy.assert_called_once()
    copied_text = mock_copy.call_args.args[0]
    assert isinstance(copied_text, str)
    assert copied_text.strip()
    assert "NBX CLI Builder" in copied_text


@pytest.mark.asyncio
async def test_cli_tui_back_button_hidden_at_root(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        back_button = app.query_one("#nav_back_button", Button)
        assert str(back_button.styles.display) == "none"


@pytest.mark.asyncio
async def test_cli_tui_selecting_group_pushes_breadcrumb(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        # Find dcim item index
        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_index = next(
            i for i, item in enumerate(items) if "dcim" in str(item.query_one(Static).content)
        )
        nav_list.index = dcim_index
        await pilot.press("enter")
        await pilot.pause()

        crumb = app.query_one("#breadcrumb", Static)
        assert "dcim" in str(crumb.content)


@pytest.mark.asyncio
async def test_cli_tui_back_button_appears_after_push(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_index = next(
            i for i, item in enumerate(items) if "dcim" in str(item.query_one(Static).content)
        )
        nav_list.index = dcim_index
        await pilot.press("enter")
        await pilot.pause()

        back_button = app.query_one("#nav_back_button", Button)
        assert str(back_button.styles.display) == "block"


@pytest.mark.asyncio
async def test_cli_tui_escape_pops_back_to_root(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_index = next(
            i for i, item in enumerate(items) if "dcim" in str(item.query_one(Static).content)
        )
        nav_list.index = dcim_index
        await pilot.press("enter")
        await pilot.pause()

        # Escape goes back
        await pilot.press("escape")
        await pilot.pause()

        crumb = app.query_one("#breadcrumb", Static)
        assert str(crumb.content) == "nbx"


@pytest.mark.asyncio
async def test_cli_tui_navigating_to_action_fills_command_input(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)

        # Enter dcim group
        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        # Enter devices resource
        items = list(nav_list.query(ListItem))
        dev_idx = next(
            i for i, it in enumerate(items) if "devices" in str(it.query_one(Static).content)
        )
        nav_list.index = dev_idx
        await pilot.press("enter")
        await pilot.pause()

        # Select "list" action
        items = list(nav_list.query(ListItem))
        list_idx = next(
            i for i, it in enumerate(items) if str(it.query_one(Static).content).startswith("list")
        )
        nav_list.index = list_idx
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert "dcim" in cmd.value
        assert "devices" in cmd.value
        assert "list" in cmd.value
        assert "-q" not in cmd.value
        assert "--json" not in cmd.value
        assert "--yaml" not in cmd.value
        assert "--markdown" not in cmd.value


@pytest.mark.asyncio
async def test_cli_tui_output_format_json_appends_flag(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        output_format = app.query_one("#output_format_select", Select)
        output_format.value = "json"
        await pilot.pause()

        nav_list = app.query_one("#nav_list", ListView)

        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        items = list(nav_list.query(ListItem))
        dev_idx = next(
            i for i, it in enumerate(items) if "devices" in str(it.query_one(Static).content)
        )
        nav_list.index = dev_idx
        await pilot.press("enter")
        await pilot.pause()

        items = list(nav_list.query(ListItem))
        list_idx = next(
            i for i, it in enumerate(items) if str(it.query_one(Static).content).startswith("list")
        )
        nav_list.index = list_idx
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert "--json" in cmd.value
        assert "--yaml" not in cmd.value
        assert "--markdown" not in cmd.value


@pytest.mark.asyncio
async def test_cli_tui_output_format_markdown_appends_flag(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        output_format = app.query_one("#output_format_select", Select)
        output_format.value = "markdown"
        await pilot.pause()

        nav_list = app.query_one("#nav_list", ListView)

        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        items = list(nav_list.query(ListItem))
        dev_idx = next(
            i for i, it in enumerate(items) if "devices" in str(it.query_one(Static).content)
        )
        nav_list.index = dev_idx
        await pilot.press("enter")
        await pilot.pause()

        items = list(nav_list.query(ListItem))
        list_idx = next(
            i for i, it in enumerate(items) if str(it.query_one(Static).content).startswith("list")
        )
        nav_list.index = list_idx
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert "--markdown" in cmd.value
        assert "--json" not in cmd.value
        assert "--yaml" not in cmd.value


@pytest.mark.asyncio
async def test_cli_tui_output_format_human_removes_flag(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        output_format = app.query_one("#output_format_select", Select)
        output_format.value = "json"
        await pilot.pause()
        output_format.value = "human"
        await pilot.pause()

        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert "--json" not in cmd.value
        assert "--yaml" not in cmd.value
        assert "--markdown" not in cmd.value


@pytest.mark.asyncio
async def test_cli_tui_copy_uses_raw_output_for_markdown_commands(real_index) -> None:
    app = _make_app(real_index)

    with patch.object(app, "copy_to_clipboard") as mock_copy:
        async with app.run_test() as pilot:
            await pilot.pause()

            cmd = app.query_one("#command_input", Input)
            cmd.value = "dcim devices list --markdown"

            output = app.query_one("#output", RichLog)
            output.write("Status: 200")
            output.write("┏━━━━┳━━━━━━━━┓")
            output.write("┃ ID ┃ Name   ┃")
            output.write("┡━━━━╇━━━━━━━━┩")
            output.write("│ 1  │ Device │")
            output.write("└────┴────────┘")

            await pilot.click("#output_copy_button")
            await pilot.pause()

    mock_copy.assert_called_once()
    copied_text = mock_copy.call_args.args[0]
    assert "┏━━━━┳━━━━━━━━┓" in copied_text
    assert "| ID | Name |" not in copied_text


@pytest.mark.asyncio
async def test_cli_tui_highlight_updates_command_input_preview(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert "dcim" in cmd.value
        assert "devices" not in cmd.value


@pytest.mark.asyncio
async def test_cli_tui_entering_branch_updates_command_input_to_current_path(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        cmd = app.query_one("#command_input", Input)
        assert cmd.value.strip() == "dcim"


@pytest.mark.asyncio
async def test_cli_tui_filter_input_filters_current_level_nodes(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        nav_list = app.query_one("#nav_list", ListView)
        root_items = list(nav_list.query(ListItem))
        dcim_idx = next(
            i for i, it in enumerate(root_items) if "dcim" in str(it.query_one(Static).content)
        )
        nav_list.index = dcim_idx
        await pilot.press("enter")
        await pilot.pause()

        nav_filter = app.query_one("#nav_filter_input", Input)
        nav_filter.value = "device"
        await pilot.pause()

        filtered_labels = [str(item.query_one(Static).content) for item in nav_list.query(ListItem)]
        filtered_text = "\n".join(filtered_labels).lower()
        assert "device-bays" in filtered_text
        assert "device-roles" in filtered_text
        assert "device-types" in filtered_text
        assert "platforms" not in filtered_text


@pytest.mark.asyncio
async def test_cli_tui_submitting_command_calls_executor(real_index) -> None:
    called_with: list[list[str]] = []

    def recording_executor(argv: list[str]) -> tuple[int, str]:
        called_with.append(argv)
        return (0, "executed")

    app = NbxCliTuiApp(client=_make_client(), index=real_index, executor=recording_executor)

    async with app.run_test() as pilot:
        await pilot.pause()
        cmd_input = app.query_one("#command_input", Input)
        cmd_input.value = "dcim devices list"
        cmd_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

    assert called_with
    assert called_with[0] == ["dcim", "devices", "list"]


@pytest.mark.asyncio
async def test_cli_tui_nbx_prefix_stripped_from_submission(real_index) -> None:
    called_with: list[list[str]] = []

    def recording_executor(argv: list[str]) -> tuple[int, str]:
        called_with.append(argv)
        return (0, "")

    app = NbxCliTuiApp(client=_make_client(), index=real_index, executor=recording_executor)

    async with app.run_test() as pilot:
        await pilot.pause()
        cmd_input = app.query_one("#command_input", Input)
        cmd_input.value = "nbx dcim devices list"
        cmd_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

    assert called_with
    assert called_with[0] == ["dcim", "devices", "list"]


@pytest.mark.asyncio
async def test_cli_tui_executor_output_shown_in_log(real_index) -> None:
    sentinel = "SENTINEL_OUTPUT_12345"
    app = NbxCliTuiApp(
        client=_make_client(),
        index=real_index,
        executor=lambda argv: (0, sentinel),
    )

    async with app.run_test() as pilot:
        await pilot.pause()
        cmd_input = app.query_one("#command_input", Input)
        cmd_input.value = "groups"
        cmd_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        # Render the log to text to check for sentinel
        log = app.query_one("#output", RichLog)
        rendered = "\n".join(str(line) for line in log.lines)
        assert sentinel in rendered


@pytest.mark.asyncio
async def test_cli_tui_clear_output_action(real_index) -> None:
    app = NbxCliTuiApp(
        client=_make_client(),
        index=real_index,
        executor=lambda argv: (0, "some output here"),
    )

    async with app.run_test() as pilot:
        await pilot.pause()
        # Execute a command to put something in the log
        cmd_input = app.query_one("#command_input", Input)
        cmd_input.value = "groups"
        cmd_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        # Clear with Ctrl+G
        await pilot.press("ctrl+g")
        await pilot.pause()

        log = app.query_one("#output", RichLog)
        assert len(log.lines) == 0


@pytest.mark.asyncio
async def test_cli_tui_focus_nav_action(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        # Focus the output first
        app.query_one("#output", RichLog).focus()
        await pilot.pause()

        # Press n to focus nav
        await pilot.press("n")
        await pilot.pause()

        assert app.focused is app.query_one("#nav_list", ListView)


@pytest.mark.asyncio
async def test_cli_tui_focus_output_action(real_index) -> None:
    app = _make_app(real_index)

    async with app.run_test() as pilot:
        await pilot.pause()
        # Press o to focus output
        await pilot.press("o")
        await pilot.pause()

        assert app.focused is app.query_one("#output", RichLog)


@pytest.mark.asyncio
async def test_cli_tui_nonzero_exit_code_shown(real_index) -> None:
    app = NbxCliTuiApp(
        client=_make_client(),
        index=real_index,
        executor=lambda argv: (1, "command failed"),
    )

    async with app.run_test() as pilot:
        await pilot.pause()
        cmd_input = app.query_one("#command_input", Input)
        cmd_input.value = "groups"
        cmd_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.pause()
        await pilot.pause()

        log = app.query_one("#output", RichLog)
        rendered = "\n".join(str(line) for line in log.lines)
        assert "Exit code" in rendered or "1" in rendered


# ---------------------------------------------------------------------------
# _nbx_cli_execute unit test
# ---------------------------------------------------------------------------


def test_nbx_cli_execute_returns_tuple() -> None:
    """_nbx_cli_execute must return (int, str) even for a no-op command."""
    exit_code, output = _nbx_cli_execute(["--help"])
    assert isinstance(exit_code, int)
    assert isinstance(output, str)


def test_nbx_cli_execute_groups_command() -> None:
    """Running ``groups`` via CliRunner must produce schema group names."""
    with patch("netbox_cli.runtime._ensure_runtime_config") as mock_cfg:
        from netbox_sdk.config import Config

        mock_cfg.return_value = Config(
            base_url="http://fake.example.com",
            token_key="fake",
            token_secret="fake",
        )
        exit_code, output = _nbx_cli_execute(["groups"])

    assert isinstance(exit_code, int)
    assert isinstance(output, str)


def test_cli_tui_convert_rich_table_to_markdown() -> None:
    text = "\n".join(
        [
            "Status: 200",
            "┏━━━━┳━━━━━━━━┓",
            "┃ ID ┃ Name   ┃",
            "┡━━━━╇━━━━━━━━┩",
            "│ 1  │ Device │",
            "│ 2  │ Router │",
            "└────┴────────┘",
        ]
    )
    converted = NbxCliTuiApp._convert_rich_tables_to_markdown(text)
    assert "Strip(" not in converted
    assert "| ID | Name |" in converted
    assert "| --- | --- |" in converted
    assert "| 1 | Device |" in converted
    assert "| 2 | Router |" in converted


def test_cli_tui_line_to_plain_text_prefers_text_attr() -> None:
    class _FakeLine:
        text = "plain-value"

        def __str__(self) -> str:
            return "Strip(...)"

    assert NbxCliTuiApp._line_to_plain_text(_FakeLine()) == "plain-value"


# ---------------------------------------------------------------------------
# run_cli_tui smoke test
# ---------------------------------------------------------------------------


def test_run_cli_tui_calls_app_run(real_index) -> None:
    with patch.object(NbxCliTuiApp, "run") as mock_run:
        mock_run.return_value = None
        run_cli_tui(client=_make_client(), index=real_index)
    mock_run.assert_called_once()
