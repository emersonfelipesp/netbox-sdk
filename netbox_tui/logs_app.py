"""Dedicated Textual app for viewing nbx application logs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import Button, DataTable, Footer, Select, Static

from netbox_sdk.logging_runtime import LogEntry, log_file_path, read_log_entries
from netbox_tui.app import TOPBAR_CLI_LABEL
from netbox_tui.chrome import (
    apply_theme,
    get_theme_catalog,
    initialize_theme_state,
    logo_renderable,
    strip_theme_select_prefix,
    update_clock_widget,
)
from netbox_tui.widgets import NbxButton


@dataclass(slots=True)
class LogViewerState:
    theme_name: str | None = None


class NetBoxLogsTuiApp(App[None]):
    TITLE = "NetBox CLI Logs"
    SUB_TITLE = "Application log viewer"
    CSS_PATH = [
        str(Path(__file__).resolve().parent / "ui_common.tcss"),
        str(Path(__file__).resolve().parent / "logs_tui.tcss"),
    ]

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("r", "refresh_logs", "Refresh", priority=True),
    ]

    def __init__(self, theme_name: str | None = None, limit: int = 200) -> None:
        super().__init__()
        self.state = LogViewerState()
        self.limit = limit
        self.log_path = log_file_path()
        self.entries: list[LogEntry] = []
        self._clock_timer: Timer | None = None
        self.theme_catalog, self.theme_name, self.theme_options = initialize_theme_state(
            self,
            requested_theme_name=theme_name,
            persisted_theme_name=self.state.theme_name,
        )

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
            with Horizontal(id="topbar_center"):
                yield Static(self._logo_renderable(), id="topbar_logo")
                yield Static(TOPBAR_CLI_LABEL, id="topbar_cli_suffix")
            with Horizontal(id="topbar_right"):
                yield Static("", id="clock")
                yield Static(f"Log: {self.log_path}", id="context_line")
                yield NbxButton(
                    "Refresh",
                    id="refresh_logs_button",
                    size="small",
                    tone="secondary",
                    classes="nbx-topbar-control",
                )
                yield NbxButton(
                    "Close",
                    id="close_tui_button",
                    size="small",
                    tone="error",
                    classes="nbx-topbar-control",
                )

        with Horizontal(id="logs_shell"):
            with Vertical(id="logs_main"):
                yield Static("Recent application logs", id="logs_controls")
                table = DataTable(id="logs_table")
                table.cursor_type = "row"
                yield table
                yield Static("", id="logs_status")
            with Vertical(id="logs_detail_panel"):
                yield Static("Entry details", id="logs_detail_title")
                yield Static("Select a log row to inspect it.", id="logs_detail")

        yield Footer()

    def on_mount(self) -> None:
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        self._update_clock()
        self.action_refresh_logs()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_logs_clock")

    def on_unmount(self) -> None:
        if self._clock_timer is not None:
            self._clock_timer.stop()
            self._clock_timer = None

    def action_refresh_logs(self) -> None:
        self.entries = read_log_entries(limit=self.limit)
        self._render_entries()

    @on(DataTable.RowSelected, "#logs_table")
    def on_row_selected(self) -> None:
        table = self.query_one("#logs_table", DataTable)
        row_index = table.cursor_row
        if row_index is None or row_index < 0 or row_index >= len(self.entries):
            return
        self._render_detail(self.entries[row_index])

    @on(Select.Changed, "#theme_select")
    def on_theme_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = self.theme_catalog.resolve(str(event.value))
        if not selected or selected == self.theme_name:
            return
        self._apply_theme(selected, notify=True)
        self.call_after_refresh(self._strip_theme_select_prefix)

    @on(Button.Pressed, "#refresh_logs_button")
    def on_refresh_pressed(self) -> None:
        self.action_refresh_logs()

    @on(Button.Pressed, "#close_tui_button")
    def on_close_pressed(self) -> None:
        self.exit()

    def _render_entries(self) -> None:
        table = self.query_one("#logs_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Time", "Level", "Logger", "Message")
        if not self.entries:
            table.add_row("-", "-", "-", "No log entries yet")
            self.query_one("#logs_status", Static).update(f"No logs found at {self.log_path}")
            self.query_one("#logs_detail", Static).update("No log entries yet.")
            return

        for entry in self.entries:
            table.add_row(
                entry.timestamp or "-",
                entry.level,
                entry.logger.replace("netbox_cli.", ""),
                entry.message,
            )

        self.query_one("#logs_status", Static).update(
            f"Loaded {len(self.entries)} log entries from {self.log_path}"
        )
        self._render_detail(self.entries[-1])

    def _render_detail(self, entry: LogEntry) -> None:
        lines = [
            f"Time: {entry.timestamp or '-'}",
            f"Level: {entry.level}",
            f"Logger: {entry.logger}",
        ]
        if entry.module:
            source = entry.module
            if entry.function:
                source = f"{source}.{entry.function}"
            if entry.line:
                source = f"{source}:{entry.line}"
            lines.append(f"Source: {source}")
        lines.append("")
        lines.append(entry.message or "<empty>")
        if entry.exception:
            lines.extend(["", entry.exception])
        self.query_one("#logs_detail", Static).update("\n".join(lines))

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

    def _logo_renderable(self):
        return logo_renderable(self.theme_catalog, self.theme_name)

    def _strip_theme_select_prefix(self) -> None:
        strip_theme_select_prefix(self, selector="#theme_select SelectCurrent Static#label")

    def _update_clock(self) -> None:
        update_clock_widget(self, widget_id="#clock")


def available_theme_names() -> tuple[str, ...]:
    return get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return get_theme_catalog().resolve(theme_name)


def run_logs_tui(theme_name: str | None = None, limit: int = 200) -> None:
    NetBoxLogsTuiApp(theme_name=theme_name, limit=limit).run()
