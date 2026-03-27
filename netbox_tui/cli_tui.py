"""Interactive CLI command builder TUI - ``nbx cli tui``.

Presents a navigable menu tree (group -> resource -> action) that
progressively builds an ``nbx`` command. When the user reaches a leaf
action the pre-built command is placed into an editable input; pressing
Enter executes it via :class:`typer.testing.CliRunner` and streams the
output into the scrollable log panel.
"""

from __future__ import annotations

import inspect
import re
import shlex
import traceback
from collections.abc import Callable
from pathlib import Path

from rich.style import Style
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Input,
    ListItem,
    ListView,
    RichLog,
    Select,
    Static,
)
from textual.worker import Worker, WorkerState

from netbox_sdk.client import ConnectionProbe, NetBoxApiClient
from netbox_sdk.logging_runtime import get_logger
from netbox_sdk.schema import SchemaIndex
from netbox_tui.app import TOPBAR_CLI_LABEL
from netbox_tui.chrome import (
    SWITCH_TO_CLI_TUI,
    SWITCH_TO_DEV_TUI,
    SWITCH_TO_DJANGO_TUI,
    SWITCH_TO_MAIN_TUI,
    apply_theme,
    badge_state_for_probe,
    get_theme_catalog,
    initialize_theme_state,
    logo_renderable,
    set_connection_badge_state,
    strip_theme_select_prefix,
    update_clock_widget,
)
from netbox_tui.cli_completions import CliCommandNode, nbx_root_command_nodes
from netbox_tui.state import TuiState, load_tui_state, save_tui_state
from netbox_tui.widgets import ContextBreadcrumb, NbxButton, SupportModal

_CLI_TUI_WORKER_GROUP = "nbx_cli_tui"
_WORKER_EXECUTE = "nbx_cli_execute"
_VIEW_MODE_OPTIONS = (
    ("- TUI", "main"),
    ("- CLI", "cli"),
    ("- Dev", "dev"),
    ("- Models", "django"),
)
_OUTPUT_FORMAT_OPTIONS = (
    ("Output - Human-Readable", "human"),
    ("Output - JSON", "json"),
    ("Output - YAML", "yaml"),
    ("Output - Markdown", "markdown"),
)
_OUTPUT_FORMAT_FLAGS = {
    "human": "",
    "json": "--json",
    "yaml": "--yaml",
    "markdown": "--markdown",
}
logger = get_logger(__name__)


class NbxCliTuiApp(App[None]):
    """Interactive CLI command builder.

    Navigate group -> resource -> action on the left panel to compose an
    ``nbx`` command, then edit and run it. Results appear in the right panel.
    """

    TITLE = "NetBox CLI"
    SUB_TITLE = "Interactive command builder"
    AUTO_FOCUS = "ListView#nav_list"
    CSS_PATH = [
        str(Path(__file__).resolve().parent / "ui_common.tcss"),
        str(Path(__file__).resolve().parent / "tui.tcss"),
    ]
    CSS = """
    #cli_main_content {
        height: 1fr;
        background: $background;
        margin: 0 1 0 1;
    }

    #nav_panel {
        width: 42%;
        height: 100%;
        border-right: tall $nb-border-subtle;
        padding: 0 1 0 0;
    }

    #nav_header {
        height: auto;
        padding: 1 1 1 1;
        color: $nb-muted-text;
    }

    #breadcrumb {
        height: auto;
        padding: 0 1;
        color: $primary;
        text-style: bold;
    }

    #nav_filter_input {
        width: 1fr;
        height: auto;
        margin: 0 1 0 1;
        border: tall $nb-border-subtle;
        background: $panel;
        color: $foreground;
        padding: 0 1;
    }

    #nav_filter_input:focus {
        border: tall $primary;
        background: $surface;
    }

    #nav_filter_input > .input--placeholder {
        color: $nb-muted-text;
    }

    #nav_list {
        width: 100%;
        height: 1fr;
        border: tall transparent;
        background: $background;
    }

    #nav_list:focus {
        border: tall $primary;
    }

    #nav_list > ListItem {
        padding: 0 1;
        background: $background;
    }

    #nav_list > ListItem:hover {
        background: $primary 10%;
    }

    #nav_back_button {
        width: auto;
        min-width: 10;
        margin: 0 1 1 1;
        display: none;
    }

    #output_format_select {
        width: 32;
    }

    #output_panel {
        width: 58%;
        height: 100%;
        padding: 0 0 0 1;
    }

    #output_header {
        width: 1fr;
        height: auto;
        padding: 1 1 1 1;
        color: $nb-muted-text;
        align: left middle;
    }

    #output_title {
        width: 1fr;
    }

    #output_copy_button {
        width: auto;
        min-width: 8;
    }

    #output_header_spacer {
        width: 1fr;
    }

    #output {
        width: 100%;
        height: 1fr;
        border: tall transparent;
        background: $background;
        padding: 0 1;
    }

    #output:focus {
        border: tall $secondary;
    }

    #status_bar {
        height: auto;
        min-height: 1;
        padding: 0 2;
        color: $warning;
        background: $background;
    }

    #cmd_bar {
        width: 1fr;
        height: auto;
        padding: 0 1 1 1;
        align: left middle;
    }

    #cmd_prompt {
        width: auto;
        min-width: 3;
        margin-right: 1;
        color: $primary;
        text-style: bold;
        content-align: left middle;
    }

    #command_input {
        width: 1fr;
        border: tall $nb-border-subtle;
        background: $panel;
        color: $foreground;
        padding: 0 1;
    }

    #command_input:focus {
        border: tall $primary;
        background: $surface;
    }

    #command_input > .input--placeholder {
        color: $nb-muted-text;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("escape", "go_back", "Back", show=True, priority=True),
        Binding("ctrl+g", "clear_output", "Clear Output", show=True),
        Binding("n", "focus_nav", "Nav", show=True),
        Binding("o", "focus_output", "Output", show=True),
    ]

    def __init__(
        self,
        client: NetBoxApiClient,
        index: SchemaIndex,
        executor: Callable[[list[str]], tuple[int, str]],
        theme_name: str | None = None,
    ) -> None:
        super().__init__()
        self.client = client
        self._index = index
        self._executor = executor
        self._state_scope = self.client.config.base_url
        self.state: TuiState = load_tui_state(self._state_scope)
        self.theme_catalog, self.theme_name, self.theme_options = initialize_theme_state(
            self,
            requested_theme_name=theme_name,
            persisted_theme_name=self.state.theme_name,
        )

        root_nodes = nbx_root_command_nodes(index)
        self._nav_stack: list[tuple[str, list[CliCommandNode]]] = [("nbx", root_nodes)]
        self._argv_fragments: list[list[str]] = [[]]
        self._nav_filter_query: str = ""

        self._active_worker: Worker | None = None
        self._clock_timer: Timer | None = None
        self._connection_timer: Timer | None = None
        self._last_connection_probe: ConnectionProbe | None = None
        self._output_format: str = "human"

    @property
    def _current_nodes(self) -> list[CliCommandNode]:
        return self._nav_stack[-1][1]

    @property
    def _current_argv(self) -> list[str]:
        argv: list[str] = []
        for frag in self._argv_fragments:
            argv.extend(frag)
        return argv

    @property
    def _breadcrumb_text(self) -> str:
        return " > ".join(label for label, _ in self._nav_stack)

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            with Horizontal(id="topbar_left"):
                yield Static("●", id="nav_dot")
                yield Select(
                    options=self.theme_options,
                    value=self.theme_name,
                    prompt="Theme",
                    id="theme_select",
                )
                yield Select(
                    options=_VIEW_MODE_OPTIONS,
                    value="cli",
                    prompt="View",
                    id="view_select",
                )
            with Horizontal(id="topbar_center"):
                yield Static(self._logo_renderable(), id="topbar_logo")
                yield Static(TOPBAR_CLI_LABEL, id="topbar_cli_suffix")
            with Horizontal(id="topbar_right"):
                yield Static("", id="clock")
                yield Static("●", id="connection_badge", classes="-checking")
                yield ContextBreadcrumb(id="context_breadcrumb")
                yield NbxButton(
                    "Liked it? Support me!",
                    id="support_button",
                    size="small",
                    tone="muted",
                    classes="nbx-topbar-control",
                )
                yield NbxButton(
                    "Close",
                    id="close_tui_button",
                    size="small",
                    tone="error",
                    classes="nbx-topbar-control",
                )

        with Horizontal(id="cli_main_content"):
            with Vertical(id="nav_panel"):
                yield Static(
                    "Commands  ↑↓ navigate · Enter select · Esc back",
                    id="nav_header",
                )
                yield Static(self._breadcrumb_text, id="breadcrumb")
                yield Input(
                    id="nav_filter_input",
                    placeholder="Filter commands (e.g. device)",
                )
                yield ListView(id="nav_list")
                yield NbxButton(
                    "← Back",
                    id="nav_back_button",
                    size="small",
                    tone="warning",
                )
            with Vertical(id="output_panel"):
                with Horizontal(id="output_header"):
                    yield Select(
                        options=_OUTPUT_FORMAT_OPTIONS,
                        value=self._output_format,
                        prompt="",
                        id="output_format_select",
                        classes="nbx-topbar-control",
                    )
                    yield Static("", id="output_header_spacer")
                    yield NbxButton("Copy", id="output_copy_button", size="small", tone="muted")
                yield RichLog(id="output", wrap=True, markup=False, auto_scroll=True)

        yield Static("", id="status_bar")
        with Horizontal(id="cmd_bar"):
            yield Static("▶", id="cmd_prompt")
            yield Input(
                id="command_input",
                placeholder="Navigate to a command above - or type here and press Enter",
            )
        yield Footer()

    def on_mount(self) -> None:
        logger.info("cli tui mounted")
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        try:
            self.query_one("#output_format_select", Select).value = self._output_format
        except NoMatches:
            pass
        self._update_clock()
        self._set_connection_badge_checking()
        self._update_context_line()
        self._probe_connection_health()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_cli_clock")
        self._connection_timer = self.set_interval(
            30.0,
            self._probe_connection_health,
            name="nbx_cli_connection_health",
        )
        self._refresh_nav()
        self._write_welcome()

    def on_unmount(self) -> None:
        logger.info("cli tui unmounting")
        self.workers.cancel_group(self, _CLI_TUI_WORKER_GROUP)
        if self._clock_timer is not None:
            self._clock_timer.stop()
            self._clock_timer = None
        if self._connection_timer is not None:
            self._connection_timer.stop()
            self._connection_timer = None
        self.state.theme_name = self.theme_name
        save_tui_state(self.state, self._state_scope)

    def _refresh_nav(self) -> None:
        nav_list = self.query_one("#nav_list", ListView)
        nav_list.clear()

        visible_nodes = self._filtered_nodes()
        for node in visible_nodes:
            item = ListItem(Static(self._styled_nav_label(node)))
            item._cli_node = node  # type: ignore[attr-defined]
            nav_list.append(item)

        if not visible_nodes:
            no_match_item = ListItem(Static("No matching commands", classes="nav-empty"))
            no_match_item._cli_node = None  # type: ignore[attr-defined]
            no_match_item._cli_placeholder = True  # type: ignore[attr-defined]
            nav_list.append(no_match_item)

        try:
            back_button = self.query_one("#nav_back_button", Button)
            back_button.styles.display = "block" if len(self._nav_stack) > 1 else "none"
        except NoMatches:
            pass

        try:
            self.query_one("#breadcrumb", Static).update(self._breadcrumb_text)
        except NoMatches:
            pass
        self._update_context_line()

    def _filtered_nodes(self) -> list[CliCommandNode]:
        query = self._nav_filter_query.strip().lower()
        if not query:
            return list(self._current_nodes)
        return [
            node
            for node in self._current_nodes
            if query in node.label.lower() or query in node.description.lower()
        ]

    def _push_level(self, node: CliCommandNode) -> None:
        self._nav_stack.append((node.label, list(node.children)))
        self._argv_fragments.append(list(node.enter_tail))
        self._nav_filter_query = ""
        try:
            self.query_one("#nav_filter_input", Input).value = ""
        except NoMatches:
            pass
        self._refresh_nav()
        self._fill_current_path_command()
        try:
            self.query_one("#nav_list", ListView).focus()
        except NoMatches:
            pass

    def _pop_level(self) -> None:
        if len(self._nav_stack) <= 1:
            return
        self._nav_stack.pop()
        self._argv_fragments.pop()
        self._nav_filter_query = ""
        try:
            self.query_one("#nav_filter_input", Input).value = ""
        except NoMatches:
            pass
        self._refresh_nav()
        self._fill_current_path_command()
        try:
            self.query_one("#nav_list", ListView).focus()
        except NoMatches:
            pass

    def _fill_current_path_command(self) -> None:
        """Reflect the currently selected breadcrumb path in the input box."""
        argv = self._with_output_format(self._current_argv)
        self._set_command_input_value(shlex.join(argv), focus=False)

    def _set_command_input_value(self, value: str, *, focus: bool) -> None:
        """Set command input text, optionally focusing the input widget."""
        try:
            input_w = self.query_one("#command_input", Input)
            input_w.value = value
            input_w.action_end()
            if focus:
                input_w.focus()
        except NoMatches:
            pass

    def _preview_command_for_node(self, node: CliCommandNode) -> None:
        """Preview the command path for the highlighted node without changing focus."""
        argv = self._current_argv + list(node.enter_tail if node.children else node.tail)
        argv = self._with_output_format(argv)
        self._set_command_input_value(shlex.join(argv), focus=False)

    def _fill_command(self, node: CliCommandNode, *, focus: bool = True) -> None:
        argv = self._current_argv + list(node.tail)
        argv = self._with_output_format(argv)
        cmd = shlex.join(argv)

        hints: list[str] = []
        if node.requires_id:
            hints.append("--id N")
        if node.allows_body:
            hints.append('--body-json {"field": "value"}')
        if hints:
            cmd = cmd + "  " + "  ".join(hints)

        self._set_command_input_value(cmd, focus=focus)

    def _with_output_format(self, argv: list[str]) -> list[str]:
        cleaned = [token for token in argv if token not in ("--json", "--yaml", "--markdown")]
        flag = _OUTPUT_FORMAT_FLAGS.get(self._output_format, "")
        if flag:
            cleaned.append(flag)
        return cleaned

    def _command_uses_markdown(self) -> bool:
        try:
            command_input = self.query_one("#command_input", Input)
        except NoMatches:
            return False

        current = command_input.value.strip()
        if not current:
            return False

        try:
            argv = shlex.split(current)
        except ValueError:
            return False
        return "--markdown" in argv

    def _sync_command_input_output_format(self) -> None:
        try:
            command_input = self.query_one("#command_input", Input)
        except NoMatches:
            return

        current = command_input.value.strip()
        if not current:
            self._fill_current_path_command()
            return

        try:
            argv = shlex.split(current)
        except ValueError:
            return

        if not argv:
            self._fill_current_path_command()
            return

        has_nbx_prefix = argv[0] == "nbx"
        body = argv[1:] if has_nbx_prefix else argv
        body = self._with_output_format(body)
        updated = (["nbx"] + body) if has_nbx_prefix else body
        self._set_command_input_value(shlex.join(updated), focus=False)

    def _update_context_line(self) -> None:
        self.query_one("#context_breadcrumb", ContextBreadcrumb).set_crumbs(
            [(f"CLI Builder: {self._breadcrumb_text}", None, None)]
        )

    def _styled_nav_label(self, node: CliCommandNode) -> Text:
        theme = self.theme_catalog.theme_for(self.theme_name)
        # Use a single explicit arrow separator for command -> path/description rows.
        arrow = " >" if node.children and not node.description else ""
        desc_part = f" -> {node.description}" if node.description else ""
        raw = f"{node.label}{arrow}{desc_part}"
        text = Text(raw)

        label_style = Style(
            color=theme.colors["primary"] if node.children else theme.colors["secondary"],
            bold=True,
        )
        text.stylize(label_style, 0, len(node.label))

        if arrow:
            start = len(node.label)
            text.stylize(Style(color=theme.variables["nb-muted-text"]), start, start + len(arrow))

        desc_start = len(node.label) + len(arrow)
        if desc_part:
            text.stylize(
                Style(color=theme.variables["nb-muted-text"]),
                desc_start,
                len(raw),
            )

        highlights: list[tuple[str, Style]] = [
            (
                r"\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b",
                Style(color=theme.colors["success"], bold=True),
            ),
            (
                r"\b(list|get|create|update|patch|delete)\b",
                Style(color=theme.colors["accent"], bold=True),
            ),
            (
                r"(--[a-z0-9-]+|-q)\b",
                Style(color=theme.colors["warning"], bold=True),
            ),
            (
                r"\b(optional|required|payload|key=value|N)\b",
                Style(color=theme.colors["secondary"]),
            ),
        ]
        for pattern, style in highlights:
            for match in re.finditer(pattern, raw, flags=re.IGNORECASE):
                text.stylize(style, match.start(), match.end())
        return text

    def _styled_command_line(self, command: str) -> Text:
        theme = self.theme_catalog.theme_for(self.theme_name)
        raw = f"nbx {command}".strip()
        text = Text(raw)
        text.stylize(Style(color=theme.colors["primary"], bold=True), 0, 3)
        for pattern, style in (
            (r"\b(GET|POST|PUT|PATCH|DELETE)\b", Style(color=theme.colors["success"], bold=True)),
            (r"(--[a-z0-9-]+|-q)\b", Style(color=theme.colors["warning"], bold=True)),
            (
                r"\b(list|get|create|update|patch|delete)\b",
                Style(color=theme.colors["accent"], bold=True),
            ),
        ):
            for match in re.finditer(pattern, raw, flags=re.IGNORECASE):
                text.stylize(style, match.start(), match.end())
        return text

    @on(ListView.Selected, "#nav_list")
    def _on_nav_selected(self, event: ListView.Selected) -> None:
        if getattr(event.item, "_cli_placeholder", False):
            return
        node: CliCommandNode | None = getattr(event.item, "_cli_node", None)
        if node is None:
            return

        if node.children:
            self._push_level(node)
        else:
            self._fill_command(node)

    @on(ListView.Highlighted, "#nav_list")
    def _on_nav_highlighted(self, event: ListView.Highlighted) -> None:
        if getattr(event.item, "_cli_placeholder", False):
            return
        node: CliCommandNode | None = getattr(event.item, "_cli_node", None)
        if node is None:
            self._fill_current_path_command()
            return
        self._preview_command_for_node(node)

    @on(Input.Changed, "#nav_filter_input")
    def _on_nav_filter_changed(self, event: Input.Changed) -> None:
        self._nav_filter_query = event.value
        self._refresh_nav()

    @on(Input.Submitted, "#command_input")
    def _on_command_submitted(self, event: Input.Submitted) -> None:
        cmd_line = event.value.strip()
        if not cmd_line:
            return
        self._execute_command(cmd_line)

    @on(Button.Pressed, "#close_tui_button")
    def on_close_pressed(self) -> None:
        self.exit()

    @on(Button.Pressed, "#support_button")
    def on_support_pressed(self) -> None:
        self.push_screen(SupportModal())

    @on(Button.Pressed, "#nav_back_button")
    def _on_nav_back_pressed(self) -> None:
        self._pop_level()

    @on(Button.Pressed, "#output_copy_button")
    def _on_output_copy_pressed(self) -> None:
        text = self._output_text_snapshot()
        if not text:
            self.notify("No output to copy yet", severity="warning")
            return
        self.copy_to_clipboard(text)
        self.notify("Output copied to clipboard", severity="information")

    @on(Select.Changed, "#output_format_select")
    def _on_output_format_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = str(event.value)
        if selected not in _OUTPUT_FORMAT_FLAGS:
            return
        if selected == self._output_format:
            return
        self._output_format = selected
        self._sync_command_input_output_format()

    @on(Select.Changed, "#view_select")
    def on_view_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        value = str(event.value)
        if value == "main":
            self.exit(result=SWITCH_TO_MAIN_TUI)
        if value == "dev":
            self.exit(result=SWITCH_TO_DEV_TUI)
        if value == "django":
            self.exit(result=SWITCH_TO_DJANGO_TUI)

    @on(Select.Changed, "#theme_select")
    def on_theme_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = self.theme_catalog.resolve(str(event.value))
        if not selected:
            self.notify("Unknown theme selected", severity="warning")
            return
        if selected == self.theme_name:
            return
        self._apply_theme(selected, notify=True)
        self.call_after_refresh(self._strip_theme_select_prefix)

    @on(Worker.StateChanged)
    def _on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        w = event.worker
        if w is not self._active_worker:
            return
        if event.state not in (WorkerState.SUCCESS, WorkerState.ERROR, WorkerState.CANCELLED):
            return

        self._active_worker = None

        try:
            self.query_one("#status_bar", Static).update("")
        except NoMatches:
            pass

        if event.state == WorkerState.CANCELLED:
            return

        try:
            output_log = self.query_one("#output", RichLog)
        except NoMatches:
            return

        if event.state == WorkerState.SUCCESS:
            try:
                exit_code, output = w.result
            except Exception as exc:
                output_log.write(Text(f"Result error: {exc!r}", style=Style(bold=True)))
                return
            if output:
                output_log.write(Text.from_ansi(output.rstrip("\n")))
            if exit_code != 0:
                output_log.write(Text(f"Exit code: {exit_code}", style=Style(bold=True)))
        elif event.state == WorkerState.ERROR and w.error is not None:
            output_log.write(Text(f"Worker error: {w.error!r}", style=Style(bold=True)))

    def action_go_back(self) -> None:
        if len(self._nav_stack) > 1:
            self._pop_level()
        else:
            try:
                self.query_one("#command_input", Input).value = ""
            except NoMatches:
                pass

    def action_clear_output(self) -> None:
        try:
            self.query_one("#output", RichLog).clear()
        except NoMatches:
            pass

    def action_focus_nav(self) -> None:
        try:
            self.query_one("#nav_list", ListView).focus()
        except NoMatches:
            pass

    def action_focus_output(self) -> None:
        try:
            self.query_one("#output", RichLog).focus()
        except NoMatches:
            pass

    def _execute_command(self, cmd_line: str) -> None:
        try:
            argv = shlex.split(cmd_line)
        except ValueError as exc:
            try:
                self.query_one("#output", RichLog).write(
                    Text(f"Parse error: {exc}", style=Style(bold=True))
                )
            except NoMatches:
                pass
            return

        if argv and argv[0] == "nbx":
            argv = argv[1:]

        if not argv:
            return

        try:
            status = Text("Running: ")
            status.append_text(self._styled_command_line(shlex.join(argv)))
            status.append(" ...")
            self.query_one("#status_bar", Static).update(status)
        except NoMatches:
            pass

        def _run() -> tuple[int, str]:
            return self._executor(argv)

        self._active_worker = self.run_worker(
            _run,
            name=_WORKER_EXECUTE,
            group=_CLI_TUI_WORKER_GROUP,
            thread=True,
            exit_on_error=False,
        )

    def _output_text_snapshot(self) -> str:
        """Return a plain-text snapshot of the output log for clipboard copy."""
        try:
            output_log = self.query_one("#output", RichLog)
        except NoMatches:
            return ""
        lines = getattr(output_log, "lines", [])
        plain_lines = [self._line_to_plain_text(line) for line in lines]
        plain_text = "\n".join(plain_lines).strip()
        if not plain_text:
            return ""
        if self._command_uses_markdown():
            return plain_text
        return self._convert_rich_tables_to_markdown(plain_text)

    @staticmethod
    def _line_to_plain_text(line: object) -> str:
        text = getattr(line, "text", None)
        if isinstance(text, str):
            return text
        return str(line)

    @staticmethod
    def _convert_rich_tables_to_markdown(text: str) -> str:
        lines = text.splitlines()
        if not lines:
            return text

        box_chars = "┏┓┗┛┳┻┫┣╋┡┩━│┃└┘┌┐┬┴├┤─"
        has_box_table = any(any(ch in line for ch in box_chars) for line in lines)
        if not has_box_table:
            return text

        table_rows: list[list[str]] = []
        in_table = False
        table_started = False
        result_prefix: list[str] = []
        result_suffix: list[str] = []

        for index, line in enumerate(lines):
            has_verticals = "│" in line or "┃" in line
            has_box = any(ch in line for ch in box_chars)
            if not table_started and has_box:
                in_table = True
                table_started = True

            if in_table and has_verticals:
                row = NbxCliTuiApp._parse_box_table_row(line)
                if row:
                    table_rows.append(row)
                continue

            if in_table and not has_box:
                result_suffix = lines[index:]
                break

            if not in_table:
                result_prefix.append(line)

        if len(table_rows) < 2:
            return text

        merged_rows = NbxCliTuiApp._merge_wrapped_box_rows(table_rows)
        if len(merged_rows) < 2:
            return text

        markdown_table = NbxCliTuiApp._rows_to_markdown_table(merged_rows)
        output_lines: list[str] = []
        if result_prefix:
            output_lines.extend(result_prefix)
        output_lines.append(markdown_table)
        if result_suffix:
            output_lines.extend(result_suffix)
        return "\n".join(output_lines).strip()

    @staticmethod
    def _parse_box_table_row(line: str) -> list[str]:
        parts = re.split(r"[│┃]", line)
        if len(parts) < 3:
            return []
        cells = [part.strip() for part in parts[1:-1]]
        if not cells:
            return []
        return cells

    @staticmethod
    def _merge_wrapped_box_rows(rows: list[list[str]]) -> list[list[str]]:
        if not rows:
            return rows

        width = len(rows[0])
        normalized_rows: list[list[str]] = []
        for row in rows:
            normalized = list(row[:width])
            if len(normalized) < width:
                normalized.extend([""] * (width - len(normalized)))
            normalized_rows.append(normalized)

        merged: list[list[str]] = [normalized_rows[0]]
        for row in normalized_rows[1:]:
            non_empty = [index for index, cell in enumerate(row) if cell]
            if non_empty and len(non_empty) < width and len(non_empty) <= 2:
                prev = merged[-1]
                for index in non_empty:
                    prev[index] = f"{prev[index]}<br>{row[index]}" if prev[index] else row[index]
            else:
                merged.append(row)
        return merged

    @staticmethod
    def _rows_to_markdown_table(rows: list[list[str]]) -> str:
        def _escape(cell: str) -> str:
            return cell.replace("|", "\\|")

        header = rows[0]
        body = rows[1:]
        header_line = "| " + " | ".join(_escape(cell) for cell in header) + " |"
        separator_line = "| " + " | ".join("---" for _ in header) + " |"
        body_lines = ["| " + " | ".join(_escape(cell) for cell in row) + " |" for row in body]
        return "\n".join([header_line, separator_line, *body_lines])

    def _write_welcome(self) -> None:
        try:
            log = self.query_one("#output", RichLog)
        except NoMatches:
            return
        theme = self.theme_catalog.theme_for(self.theme_name)
        title = Text("NBX CLI Builder", style=Style(color=theme.colors["primary"], bold=True))
        log.write(title)

        line1 = Text(
            "Navigate the command tree on the left to compose an ",
            style=Style(color=theme.variables["nb-muted-text"]),
        )
        line1.append("nbx", style=Style(color=theme.colors["primary"], bold=True))
        line1.append(" command.", style=Style(color=theme.variables["nb-muted-text"]))
        log.write(line1)

        line2 = Text("The built command is placed in the input below - edit then press ")
        line2.stylize(Style(color=theme.variables["nb-muted-text"]), 0, len(line2.plain))
        line2.append("Enter", style=Style(color=theme.colors["accent"], bold=True))
        line2.append(".", style=Style(color=theme.variables["nb-muted-text"]))
        log.write(line2)

        keys = Text("Esc", style=Style(color=theme.colors["warning"], bold=True))
        keys.append(
            " -> go back one level  |  ", style=Style(color=theme.variables["nb-muted-text"])
        )
        keys.append("q", style=Style(color=theme.colors["warning"], bold=True))
        keys.append(" or ", style=Style(color=theme.variables["nb-muted-text"]))
        keys.append("Ctrl+C", style=Style(color=theme.colors["warning"], bold=True))
        keys.append(" -> quit.", style=Style(color=theme.variables["nb-muted-text"]))
        log.write(keys)
        log.write(Text(""))

    def _strip_theme_select_prefix(self) -> None:
        strip_theme_select_prefix(self, selector="#theme_select SelectCurrent Static#label")
        strip_theme_select_prefix(self, selector="#view_select SelectCurrent Static#label")

    def _update_clock(self) -> None:
        update_clock_widget(self, widget_id="#clock")

    def _set_connection_badge_checking(self) -> None:
        set_connection_badge_state(self, badge_id="#connection_badge", state="checking")

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        set_connection_badge_state(
            self,
            badge_id="#connection_badge",
            state=badge_state_for_probe(probe),
        )

    async def _run_connection_probe(self) -> ConnectionProbe:
        probe_fn = getattr(self.client, "probe_connection", None)
        if callable(probe_fn):
            result = probe_fn()
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, ConnectionProbe):
                return result

        try:
            response = await self.client.request(
                "GET", "/", headers={"Content-Type": "application/json"}
            )
        except Exception as exc:  # noqa: BLE001
            return ConnectionProbe(status=0, version="", ok=False, error=str(exc))

        headers = getattr(response, "headers", {}) or {}
        version = headers.get("API-Version", "") if isinstance(headers, dict) else ""
        status = int(getattr(response, "status", 0) or 0)
        ok = status < 400 or status == 403
        return ConnectionProbe(
            status=status,
            version=version,
            ok=ok,
            error=None if ok else getattr(response, "text", ""),
        )

    @work(group="cli_connection_probe", exclusive=True, thread=False)
    async def _probe_connection_health(self) -> None:
        self._set_connection_badge_checking()
        probe = await self._run_connection_probe()
        self._last_connection_probe = probe
        self._render_connection_status(probe)

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        self.theme_name = apply_theme(
            self,
            theme_catalog=self.theme_catalog,
            theme_options=self.theme_options,
            current_theme_name=self.theme_name,
            new_theme_name=theme_name,
            state=self.state,
            logo_widget_id="#topbar_logo",
            notify=notify,
        )
        self._refresh_nav()

    def _logo_renderable(self):
        return logo_renderable(self.theme_catalog, self.theme_name)


def _nbx_cli_execute(argv: list[str]) -> tuple[int, str]:
    """Invoke the nbx Typer app via CliRunner; return (exit_code, output)."""
    from typer.testing import CliRunner  # noqa: PLC0415

    from netbox_cli import app  # noqa: PLC0415

    runner_kwargs: dict = {}
    try:
        sig = inspect.signature(CliRunner.__init__)
        if "mix_stderr" in sig.parameters:
            runner_kwargs["mix_stderr"] = False
    except (TypeError, ValueError):
        pass

    runner = CliRunner(**runner_kwargs)
    result = runner.invoke(app, argv, catch_exceptions=True, color=True)

    stdout = result.stdout or ""
    stderr = getattr(result, "stderr", "") or ""
    output = stdout + stderr

    if result.exception and not isinstance(result.exception, SystemExit):
        tb = "".join(
            traceback.format_exception(
                type(result.exception),
                result.exception,
                result.exception.__traceback__,
            )
        )
        output += f"\n{tb}"

    exit_code: int = 0
    if isinstance(result.exit_code, int):
        exit_code = result.exit_code
    elif result.exception is not None:
        exit_code = 1

    return (exit_code, output)


def available_theme_names() -> tuple[str, ...]:
    return get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return get_theme_catalog().resolve(theme_name)


def run_cli_tui(
    client: NetBoxApiClient,
    index: SchemaIndex,
    theme_name: str | None = None,
    demo_mode: bool = False,
) -> None:
    """Launch the NBX CLI Builder TUI.

    Called by ``nbx cli tui``.
    """
    try:
        next_mode = "cli"
        next_theme = theme_name
        while True:
            if next_mode == "cli":
                app = NbxCliTuiApp(
                    client=client,
                    index=index,
                    executor=_nbx_cli_execute,
                    theme_name=next_theme,
                )
                result = app.run()
                if result == SWITCH_TO_MAIN_TUI:
                    next_mode = "main"
                    next_theme = app.theme_name
                    continue
                if result == SWITCH_TO_DEV_TUI:
                    next_mode = "dev"
                    next_theme = app.theme_name
                    continue
                if result == SWITCH_TO_DJANGO_TUI:
                    from netbox_tui.django_model_app import run_django_model_tui

                    run_django_model_tui(theme_name=app.theme_name)
                    return
                return

            if next_mode == "main":
                from netbox_tui.app import NetBoxTuiApp

                app = NetBoxTuiApp(
                    client=client,
                    index=index,
                    theme_name=next_theme,
                    demo_mode=demo_mode,
                )
                result = app.run()
                if result == SWITCH_TO_DEV_TUI:
                    next_mode = "dev"
                    next_theme = app.theme_name
                    continue
                if result == SWITCH_TO_CLI_TUI:
                    next_mode = "cli"
                    next_theme = app.theme_name
                    continue
                if result == SWITCH_TO_DJANGO_TUI:
                    from netbox_tui.django_model_app import run_django_model_tui

                    run_django_model_tui(theme_name=app.theme_name)
                    return
                return

            from netbox_tui.dev_app import NetBoxDevTuiApp

            app = NetBoxDevTuiApp(client=client, index=index, theme_name=next_theme)
            result = app.run()
            if result == SWITCH_TO_MAIN_TUI:
                next_mode = "main"
                next_theme = app.theme_name
                continue
            if result == SWITCH_TO_CLI_TUI:
                next_mode = "cli"
                next_theme = app.theme_name
                continue
            if result == SWITCH_TO_DJANGO_TUI:
                from netbox_tui.django_model_app import run_django_model_tui

                run_django_model_tui(theme_name=app.theme_name)
                return
            return
    except KeyboardInterrupt:
        pass
