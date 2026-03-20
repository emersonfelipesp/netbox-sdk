from __future__ import annotations

import inspect
import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from textual import events, on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.timer import Timer
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Input,
    Select,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)

from netbox_cli.api import ConnectionProbe, NetBoxApiClient
from netbox_cli.schema import SchemaIndex
from netbox_cli.theme_registry import ThemeCatalog, load_theme_catalog

from .formatting import (
    configure_semantic_styles,
    humanize_field,
    humanize_group,
    humanize_resource,
    order_field_names,
    parse_response_rows,
    semantic_cell,
)
from .navigation import build_navigation_menus
from .panels import ObjectAttributesPanel
from .state import TuiState, ViewState, load_tui_state, save_tui_state

_THEME_CATALOG: ThemeCatalog | None = None


def _get_theme_catalog() -> ThemeCatalog:
    global _THEME_CATALOG
    if _THEME_CATALOG is None:
        _THEME_CATALOG = load_theme_catalog()
    return _THEME_CATALOG


class NetBoxTuiApp(App[None]):
    TITLE = "NetBox CLI"
    SUB_TITLE = "NetBox UI-style shell for terminal"
    CSS_PATH = str(Path(__file__).resolve().parent.parent / "tui.tcss")

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("escape", "cancel", "Cancel", show=False, priority=True),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("g", "focus_navigation", "Navigation", priority=True),
        Binding("s", "focus_results", "Results", priority=True),
        Binding("r", "refresh", "Refresh", priority=True),
        Binding("f", "filter_modal", "Filter", priority=True),
        Binding("space", "toggle_select", "Toggle Row", priority=True),
        Binding("a", "toggle_select_all", "Select All", priority=True),
        Binding("d", "show_details", "Details", priority=True),
    ]

    def __init__(
        self,
        client: NetBoxApiClient,
        index: SchemaIndex,
        theme_name: str | None = None,
        demo_mode: bool = False,
    ):
        super().__init__()
        self.client = client
        self.index = index
        self.demo_mode = demo_mode
        self.state: TuiState = load_tui_state()
        self.theme_catalog = _get_theme_catalog()
        requested_theme = (
            self.theme_catalog.resolve(theme_name) if theme_name is not None else None
        )
        state_theme = self.theme_catalog.resolve(self.state.theme_name)
        self.theme_name = (
            requested_theme or state_theme or self.theme_catalog.default_theme_name
        )
        self.theme_options = self.theme_catalog.select_options()
        active_definition = self.theme_catalog.theme_for(self.theme_name)
        configure_semantic_styles(
            colors=active_definition.colors,
            variables=active_definition.variables,
        )

        for definition in self.theme_catalog.themes:
            self.register_theme(definition.to_textual_theme())
        self.theme = self.theme_name

        self.current_group: str | None = self.state.last_view.group
        self.current_resource: str | None = self.state.last_view.resource
        self.current_rows: list[dict[str, Any]] = []
        self.selected_row_ids: set[str] = set()
        self._connection_timer: Timer | None = None
        self._clock_timer: Timer | None = None
        self._last_connection_probe: ConnectionProbe | None = None
        self._filter_fields: list[tuple[str, str]] = []
        self._filter_overlay_field: str = ""
        self._ignored_filter_select_values: set[str] = set()

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("●", id="nav_dot")
            yield Select(
                options=self.theme_options,
                value=self.theme_name,
                prompt="Theme",
                id="theme_select",
            )
            with Horizontal(id="app_title_wrap"):
                yield Static(self.TITLE, id="app_title")
                if self.demo_mode:
                    yield Static("(Demo Version)", id="app_title_demo")
            yield Static("", id="topbar_spacer")
            yield Static("", id="clock")
            yield Static(
                "● Checking connection...",
                id="connection_badge",
                classes="-checking",
            )
            yield Static("Context: <none>", id="context_line")
            yield Button("Close", id="close_tui_button")

        with Horizontal(id="query_bar"):
            yield Input(
                value=self.state.last_view.query_text,
                id="global_search",
                placeholder="Quick search: plain text -> q=<text>, or key=value",
            )
            yield Select(
                options=[("Filter Field", Select.BLANK)],
                value=Select.BLANK,
                prompt="Filter",
                id="filter_select",
            )
        yield Static("Filters: none", id="active_filters")

        with Horizontal(id="shell"):
            with Vertical(id="sidebar"):
                yield Static("Navigation", id="nav_title")
                yield Tree("NetBox", id="nav_tree")
                yield Static(
                    "/ search | g nav | s results | f filter | d details", id="nav_help"
                )

            with Vertical(id="main"):
                with TabbedContent(id="main_tabs"):
                    with TabPane("Results", id="results_tab"):
                        yield Static(
                            "Select a resource from Navigation", id="results_controls"
                        )
                        table = DataTable(id="results_table")
                        table.cursor_type = "row"
                        table.add_columns("sel", "result")
                        table.add_row("", "No data loaded")
                        yield table
                        yield Static("Ready", id="results_status")

                    with TabPane("Details", id="details_tab"):
                        yield ObjectAttributesPanel(panel_id="detail_panel")
            with Vertical(id="connection_warning_overlay", classes="hidden"):
                yield Static("", id="connection_warning")
            with Vertical(id="filter_overlay", classes="hidden"):
                with Vertical(id="filter_dialog"):
                    yield Static("Apply Filter", classes="panel-title")
                    yield Static("", id="filter_field_label")
                    yield Input(placeholder="Value", id="filter_value")
                    with Horizontal(id="filter_buttons"):
                        yield Button("Apply", id="filter_apply", variant="primary")
                        yield Button("Cancel", id="filter_cancel")

        yield Footer()

    def on_mount(self) -> None:
        self._apply_theme(self.theme_name)
        self._update_clock()
        self._set_connection_badge_checking()
        self._build_navigation_tree()
        self._update_context_line()
        self._sync_search_input()
        self._update_active_filters()
        self.query_one("#nav_tree", Tree).focus()
        self._restore_last_view_if_any()
        self._probe_connection_health()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_clock")
        self._connection_timer = self.set_interval(
            30.0,
            self._probe_connection_health,
            name="nbx_connection_health",
        )

    def on_key(self, event: events.Key) -> None:
        if isinstance(self.focused, Input):
            return

        handlers = {
            "a": self.action_toggle_select_all,
            "d": self.action_show_details,
            "f": self.action_filter_modal,
            "g": self.action_focus_navigation,
            "q": self.action_quit,
            "r": self.action_refresh,
            "s": self.action_focus_results,
            "/": self.action_focus_search,
            "space": self.action_toggle_select,
        }
        handler = handlers.get(event.key)
        if handler is None:
            return
        event.stop()
        handler()

    def on_unmount(self) -> None:
        if self._clock_timer is not None:
            self._clock_timer.stop()
            self._clock_timer = None
        if self._connection_timer is not None:
            self._connection_timer.stop()
            self._connection_timer = None
        query_text = self.state.last_view.query_text
        try:
            query_text = self.query_one("#global_search", Input).value.strip()
        except NoMatches:
            # During teardown the widget tree may already be gone.
            pass
        self.state.last_view = ViewState(
            group=self.current_group,
            resource=self.current_resource,
            query_text=query_text,
            details_expanded=False,
        )
        self.state.theme_name = self.theme_name
        save_tui_state(self.state)

    def action_focus_search(self) -> None:
        self.query_one("#global_search", Input).focus()

    def action_focus_navigation(self) -> None:
        self.query_one("#nav_tree", Tree).focus()

    def action_focus_results(self) -> None:
        self.query_one("#results_table", DataTable).focus()

    def action_refresh(self) -> None:
        if self.current_group and self.current_resource:
            self._load_rows(self.current_group, self.current_resource)

    def action_filter_modal(self) -> None:
        default_key = self._selected_filter_field()
        if not default_key and self._filter_fields:
            default_key = self._filter_fields[0][1]
        if not default_key:
            self.notify("No filterable fields loaded yet", severity="warning")
            return
        self._open_filter_overlay(default_key)

    def action_show_details(self) -> None:
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = "details_tab"

    def action_toggle_select(self) -> None:
        table = self.query_one("#results_table", DataTable)
        row_index = table.cursor_row
        if row_index is None or row_index < 0 or row_index >= len(self.current_rows):
            return

        row_id = self._row_identity(self.current_rows[row_index], row_index)
        if row_id in self.selected_row_ids:
            self.selected_row_ids.remove(row_id)
        else:
            self.selected_row_ids.add(row_id)

        self._render_results_table(self.current_rows)
        self._set_status(f"Selected {len(self.selected_row_ids)} row(s)")

    def action_toggle_select_all(self) -> None:
        if not self.current_rows:
            return
        all_ids = {
            self._row_identity(row, idx) for idx, row in enumerate(self.current_rows)
        }
        if self.selected_row_ids == all_ids:
            self.selected_row_ids.clear()
        else:
            self.selected_row_ids = set(all_ids)

        self._render_results_table(self.current_rows)
        self._set_status(f"Selected {len(self.selected_row_ids)} row(s)")

    @on(Input.Submitted, "#global_search")
    def on_search_submit(self) -> None:
        self._update_active_filters()
        if self.current_group and self.current_resource:
            self._load_rows(self.current_group, self.current_resource)

    @on(Input.Submitted, "#filter_value")
    def on_filter_value_submit(self) -> None:
        self._apply_filter_overlay()

    @on(Button.Pressed, "#close_tui_button")
    def on_close_pressed(self) -> None:
        self.exit()

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

    @on(Select.Changed, "#filter_select")
    def on_filter_select_changed(self, event: Select.Changed) -> None:
        selected = str(event.value)
        if selected in self._ignored_filter_select_values:
            self._ignored_filter_select_values.discard(selected)
            return
        if not any(field_value == selected for _, field_value in self._filter_fields):
            return
        self._open_filter_overlay(selected)

    @on(Tree.NodeSelected, "#nav_tree")
    def on_nav_selected(self, event: Tree.NodeSelected[tuple[str, str] | None]) -> None:
        if event.node.data is None:
            if event.node.children:
                event.node.toggle()
            if not event.node.children:
                self._set_status(
                    "No API endpoint is available for this menu item in TUI"
                )
            return

        group, resource = event.node.data
        self.current_group = group
        self.current_resource = resource
        self.selected_row_ids.clear()
        self._update_context_line()
        self._set_controls(
            f"Resource: {humanize_group(group)} / {humanize_resource(resource)}"
        )
        self._load_rows(group, resource)

    @on(DataTable.RowSelected, "#results_table")
    def on_row_selected(self) -> None:
        table = self.query_one("#results_table", DataTable)
        row_index = table.cursor_row
        if row_index is None or row_index < 0 or row_index >= len(self.current_rows):
            self.query_one("#detail_panel", ObjectAttributesPanel).set_object(None)
            return

        selected = self.current_rows[row_index]
        self._load_object_details(selected)
        self._refresh_filter_fields(selected.keys())
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = "details_tab"

    @on(DataTable.CellSelected, "#detail_table")
    async def on_detail_cell_selected(self, event: DataTable.CellSelected[Any]) -> None:
        if event.coordinate.column != 1:
            return

        panel = self.query_one("#detail_panel", ObjectAttributesPanel)
        row_value = panel.detail_value_at(event.coordinate.row)
        target = self._resolve_linked_object_target(row_value)
        if target is None:
            return

        group, resource, detail_path, fallback_row = target
        self.current_group = group
        self.current_resource = resource
        self.selected_row_ids.clear()
        self._update_context_line()
        self._set_controls(
            f"Resource: {humanize_group(group)} / {humanize_resource(resource)}"
        )
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = "details_tab"
        await self._show_detail_for_path(detail_path, fallback_row)

    @on(Button.Pressed, "#filter_apply")
    def on_filter_apply_pressed(self) -> None:
        self._apply_filter_overlay()

    @on(Button.Pressed, "#filter_cancel")
    def on_filter_cancel_pressed(self) -> None:
        self._close_filter_overlay()

    @work(group="list_refresh", exclusive=True, thread=False)
    async def _load_rows(self, group: str, resource: str) -> None:
        paths = self.index.resource_paths(group, resource)
        if paths is None or paths.list_path is None:
            self.current_rows = []
            self._render_results_table([])
            self._set_status("List endpoint unavailable for this resource")
            return

        query = self._query_from_search(
            self.query_one("#global_search", Input).value.strip()
        )
        self._set_status(f"Loading {group}/{resource}...")

        try:
            response = await self.client.request("GET", paths.list_path, query=query)
        except Exception as exc:  # noqa: BLE001
            self.current_rows = []
            self._render_results_table([])
            self._set_status(f"Request failed: {exc}")
            return

        rows = parse_response_rows(response.text)
        self.current_rows = rows
        self._prune_selection()
        self._render_results_table(rows)
        self._update_active_filters()

        if rows:
            self._load_object_details(rows[0])
            self._refresh_filter_fields(rows[0].keys())
        else:
            self.query_one("#detail_panel", ObjectAttributesPanel).set_object(None)
            self._refresh_filter_fields([])

        if response.status >= 400:
            self.notify(f"HTTP {response.status}", severity="error")
            self._set_status(f"HTTP {response.status}")
        else:
            self._set_status(f"Loaded {len(rows)} row(s) - HTTP {response.status}")
        self.query_one("#results_table", DataTable).focus()

    async def _show_detail_for_path(
        self, detail_path: str, fallback_row: dict[str, Any]
    ) -> None:
        panel = self.query_one("#detail_panel", ObjectAttributesPanel)
        panel.set_loading("Loading object details...")

        try:
            response = await self.client.request("GET", detail_path)
        except Exception as exc:  # noqa: BLE001
            panel.set_object(fallback_row)
            self.notify(f"Detail request failed: {exc}", severity="error")
            return

        if response.status >= 400:
            panel.set_object(fallback_row)
            self.notify(
                f"HTTP {response.status} while loading details", severity="warning"
            )
            return

        parsed = parse_response_rows(response.text)
        if not parsed:
            panel.set_object(fallback_row)
            panel.set_trace(None)
            return

        obj = parsed[0]
        panel.set_object(obj)
        await self._load_trace_for_object(obj)

    @work(group="detail_refresh", exclusive=True, thread=False)
    async def _load_object_details(self, row: dict[str, Any]) -> None:
        group = self.current_group
        resource = self.current_resource
        if not group or not resource:
            panel = self.query_one("#detail_panel", ObjectAttributesPanel)
            panel.set_object(row)
            panel.set_trace(None)
            return

        object_id = row.get("id")
        if object_id is None:
            panel = self.query_one("#detail_panel", ObjectAttributesPanel)
            panel.set_object(row)
            panel.set_trace(None)
            return

        paths = self.index.resource_paths(group, resource)
        if paths is None or paths.detail_path is None:
            panel = self.query_one("#detail_panel", ObjectAttributesPanel)
            panel.set_object(row)
            panel.set_trace(None)
            return

        detail_path = paths.detail_path.replace("{id}", str(object_id))
        await self._show_detail_for_path(detail_path, row)

    async def _load_trace_for_object(self, obj: dict[str, Any]) -> None:
        panel = self.query_one("#detail_panel", ObjectAttributesPanel)
        group = self.current_group
        resource = self.current_resource
        if not group or not resource:
            panel.set_trace(None)
            return

        object_id = obj.get("id")
        trace_template = self.index.trace_path(group, resource)
        paths_template = self.index.paths_path(group, resource)
        trace_endpoint = trace_template or paths_template
        if object_id is None or not trace_endpoint:
            panel.set_trace(None)
            return

        # Interfaces without a cable cannot yield a meaningful trace.
        if group == "dcim" and resource == "interfaces" and not obj.get("cable"):
            panel.set_trace(None)
            return

        trace_path = trace_endpoint.replace("{id}", str(object_id))
        try:
            response = await self.client.request("GET", trace_path)
        except Exception:
            panel.set_trace(None)
            return

        if response.status >= 400:
            panel.set_trace(None)
            return

        try:
            trace_payload = json.loads(response.text)
        except json.JSONDecodeError:
            panel.set_trace(None)
            return

        panel.set_trace(trace_payload)

    def _build_navigation_tree(self) -> None:
        tree = self.query_one("#nav_tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()
        for menu in build_navigation_menus(self.index):
            menu_node = root.add(menu.label)
            for group in menu.groups:
                group_node = menu_node.add(group.label)
                for item in group.items:
                    data = (
                        (item.group, item.resource)
                        if item.group and item.resource
                        else None
                    )
                    group_node.add_leaf(item.label, data=data)

    def _restore_last_view_if_any(self) -> None:
        group = self.state.last_view.group
        resource = self.state.last_view.resource
        if not group or not resource:
            return
        if resource not in self.index.resources(group):
            return

        self.current_group = group
        self.current_resource = resource
        self._update_context_line()
        self._set_controls(
            f"Resource: {humanize_group(group)} / {humanize_resource(resource)}"
        )
        self._load_rows(group, resource)

    def _sync_search_input(self) -> None:
        self.query_one("#global_search", Input).value = self.state.last_view.query_text

    def _update_clock(self) -> None:
        try:
            self.query_one("#clock", Static).update(datetime.now().strftime("%H:%M:%S"))
        except NoMatches:
            pass

    def _update_context_line(self) -> None:
        target = self.query_one("#context_line", Static)
        if self.current_group and self.current_resource:
            target.update(
                f"Context: {humanize_group(self.current_group)} / {humanize_resource(self.current_resource)}"
            )
        else:
            target.update("Context: <none>")

    def _set_controls(self, text: str) -> None:
        self.query_one("#results_controls", Static).update(text)

    def _set_status(self, text: str) -> None:
        self.query_one("#results_status", Static).update(text)

    @work(group="connection_probe", exclusive=True, thread=False)
    async def _probe_connection_health(self) -> None:
        self._set_connection_badge_checking()
        probe = await self._run_connection_probe()
        self._last_connection_probe = probe
        self._render_connection_status(probe)

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

    def _query_from_search(self, raw: str) -> dict[str, str]:
        raw = raw.strip()
        if not raw:
            return {}

        parsed: dict[str, str] = {}
        if "=" not in raw:
            return {"q": raw}

        chunks = [part.strip() for part in raw.split(",") if part.strip()]
        for chunk in chunks:
            if "=" not in chunk:
                return {"q": raw}
            key, value = chunk.split("=", 1)
            key = key.strip()
            if not key:
                continue
            parsed[key] = value

        return parsed or {"q": raw}

    def _prune_selection(self) -> None:
        valid_ids = {
            self._row_identity(row, idx) for idx, row in enumerate(self.current_rows)
        }
        self.selected_row_ids &= valid_ids

    def _render_results_table(self, rows: list[dict[str, Any]]) -> None:
        table = self.query_one("#results_table", DataTable)
        table.clear(columns=True)

        if not rows:
            table.add_columns("sel", "result")
            table.add_row("", "No results")
            return

        columns = ["sel"]
        discovered: list[str] = []
        for row in rows:
            for key in row:
                name = str(key)
                if name not in discovered:
                    discovered.append(name)
        discovered = order_field_names(discovered)
        columns.extend(humanize_field(name) for name in discovered)

        table.add_columns(*columns)

        for idx, row in enumerate(rows):
            row_id = self._row_identity(row, idx)
            marker = "●" if row_id in self.selected_row_ids else ""
            values = [marker]
            values.extend(semantic_cell(col, row.get(col)) for col in discovered)
            table.add_row(*values)

    def _row_identity(self, row: dict[str, Any], index: int) -> str:
        if "id" in row and row["id"] is not None:
            return str(row["id"])
        return f"row:{index}"

    def _refresh_filter_fields(self, fields: Iterable[str]) -> None:
        select = self.query_one("#filter_select", Select)
        current = self._selected_filter_field()
        seen: set[str] = set()
        ordered: list[tuple[str, str]] = []
        for name in order_field_names([str(field) for field in fields]):
            if name in seen:
                continue
            seen.add(name)
            ordered.append((humanize_field(name), name))

        self._filter_fields = ordered
        options: list[tuple[str, str | Select.BLANK]] = [("Filter Field", Select.BLANK)]
        options.extend(ordered)
        select.set_options(options)
        if current and any(value == current for _, value in ordered):
            self._ignored_filter_select_values.add(current)
            select.value = current
        else:
            self._ignored_filter_select_values.add(str(Select.BLANK))
            select.value = Select.BLANK
        self._update_active_filters()

    def _selected_filter_field(self) -> str:
        value = self.query_one("#filter_select", Select).value
        if value is None:
            return ""
        selected = str(value)
        if not any(field_value == selected for _, field_value in self._filter_fields):
            return ""
        return selected

    def _open_filter_overlay(self, field_name: str) -> None:
        self._filter_overlay_field = field_name
        overlay = self.query_one("#filter_overlay", Vertical)
        label = self.query_one("#filter_field_label", Static)
        value_input = self.query_one("#filter_value", Input)
        select = self.query_one("#filter_select", Select)
        self._ignored_filter_select_values.add(field_name)
        select.value = field_name
        label.update(f"Field: {humanize_field(field_name)}")
        value_input.value = self._current_filter_value(field_name)
        overlay.remove_class("hidden")
        value_input.focus()

    def _close_filter_overlay(self) -> None:
        self._filter_overlay_field = ""
        self.query_one("#filter_overlay", Vertical).add_class("hidden")
        self.query_one("#filter_value", Input).value = ""

    def _apply_filter_overlay(self) -> None:
        key = self._filter_overlay_field.strip()
        if not key:
            self.notify("Field is required", severity="warning")
            return
        value = self.query_one("#filter_value", Input).value.strip()
        self._set_filter_query(key, value)
        self._close_filter_overlay()
        if self.current_group and self.current_resource:
            self._load_rows(self.current_group, self.current_resource)
        else:
            self._update_active_filters()

    def _current_filter_value(self, key: str) -> str:
        return self._parse_filter_pairs(
            self.query_one("#global_search", Input).value.strip()
        ).get(key, "")

    def _set_filter_query(self, key: str, value: str) -> None:
        search = self.query_one("#global_search", Input)
        pairs = self._parse_filter_pairs(search.value.strip())
        if value:
            pairs[key] = value
        else:
            pairs.pop(key, None)
        search.value = ", ".join(f"{name}={pairs[name]}" for name in sorted(pairs))
        self._update_active_filters()

    def _parse_filter_pairs(self, raw: str) -> dict[str, str]:
        raw = raw.strip()
        if not raw or "=" not in raw:
            return {}
        pairs: dict[str, str] = {}
        for chunk in [part.strip() for part in raw.split(",") if part.strip()]:
            if "=" not in chunk:
                return {}
            key, value = chunk.split("=", 1)
            key = key.strip()
            if key:
                pairs[key] = value.strip()
        return pairs

    def _update_active_filters(self) -> None:
        target = self.query_one("#active_filters", Static)
        pairs = self._parse_filter_pairs(self.query_one("#global_search", Input).value)
        if not pairs:
            target.update("Filters: none")
            return
        chips = ", ".join(
            f"{humanize_field(key)}={value}" for key, value in sorted(pairs.items())
        )
        target.update(f"Filters: {chips}")

    def action_cancel(self) -> None:
        overlay = self.query_one("#filter_overlay", Vertical)
        if "hidden" not in overlay.classes:
            self._close_filter_overlay()

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        definition = self.theme_catalog.theme_for(theme_name)
        configure_semantic_styles(
            colors=definition.colors, variables=definition.variables
        )

        previous = self.theme_name
        if previous:
            self.screen.remove_class(f"theme-{previous}")
        self.theme_name = theme_name
        self.state.theme_name = theme_name
        self.theme = theme_name
        self.screen.add_class(f"theme-{theme_name}")
        if notify:
            label = next(
                (name for name, key in self.theme_options if key == theme_name),
                theme_name,
            )
            self.notify(f"Theme switched to {label}")

    def _set_connection_badge_checking(self) -> None:
        badge = self.query_one("#connection_badge", Static)
        badge.remove_class("-ok")
        badge.remove_class("-warning")
        badge.remove_class("-error")
        badge.add_class("-checking")
        badge.update("●")
        self.sub_title = "NetBox UI-style shell for terminal [checking]"

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        badge = self.query_one("#connection_badge", Static)
        overlay = self.query_one("#connection_warning_overlay", Vertical)
        warning = self.query_one("#connection_warning", Static)

        badge.remove_class("-checking")
        badge.remove_class("-ok")
        badge.remove_class("-warning")
        badge.remove_class("-error")

        version_text = probe.version or "n/a"
        if probe.status == 0:
            badge.add_class("-error")
            badge.update("●")
            self.sub_title = f"NetBox UI-style shell for terminal [down network] [API {version_text}]"
            warning.update(
                "NetBox Connection Failed\n\n"
                "Network error while reaching NetBox API base URL.\n"
                "Verify host, token, and connectivity.\n\n"
                f"Status: network error\nAPI-Version: {version_text}"
            )
            overlay.remove_class("hidden")
            return

        if probe.ok and probe.status < 300:
            badge.add_class("-ok")
            badge.update("●")
            self.sub_title = f"NetBox UI-style shell for terminal [up {probe.status}] [API {version_text}]"
            overlay.add_class("hidden")
            return

        if probe.ok and probe.status == 403:
            badge.add_class("-warning")
            badge.update("●")
            self.sub_title = f"NetBox UI-style shell for terminal [warn {probe.status}] [API {version_text}]"
            warning.update(
                "NetBox Reached with Authorization Warning\n\n"
                "Connection succeeded but token/permissions returned 403.\n"
                "Check token scope and credentials.\n\n"
                f"Status: {probe.status}\nAPI-Version: {version_text}"
            )
            overlay.remove_class("hidden")
            return

        badge.add_class("-error")
        badge.update("●")
        self.sub_title = f"NetBox UI-style shell for terminal [down {probe.status}] [API {version_text}]"
        warning.update(
            "NetBox API Request Failed\n\n"
            "NetBox endpoint responded with a failing status.\n"
            "Check URL/authentication and server health.\n\n"
            f"Status: {probe.status}\nAPI-Version: {version_text}"
        )
        overlay.remove_class("hidden")

    def _resolve_linked_object_target(
        self, value: Any
    ) -> tuple[str, str, str, dict[str, Any]] | None:
        if not isinstance(value, dict):
            return None

        raw_url = value.get("url") or value.get("display_url")
        if not isinstance(raw_url, str) or not raw_url.strip():
            return None

        parsed = urlparse(raw_url.strip())
        path = parsed.path or raw_url.strip()
        parts = [part for part in path.split("/") if part]
        if parts and parts[0] == "api":
            parts = parts[1:]
        if len(parts) < 3:
            return None

        group, resource, object_id = parts[0], parts[1], parts[2]
        if object_id == "{id}" and value.get("id") is not None:
            object_id = str(value["id"])
        if not str(object_id).isdigit():
            return None
        if self.index.resource_paths(group, resource) is None:
            return None

        detail_path = f"/api/{group}/{resource}/{object_id}/"
        fallback_row: dict[str, Any] = dict(value)
        fallback_row["id"] = int(object_id)
        if "display" not in fallback_row and "name" in fallback_row:
            fallback_row["display"] = str(fallback_row["name"])
        return group, resource, detail_path, fallback_row


def available_theme_names() -> tuple[str, ...]:
    return _get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return _get_theme_catalog().resolve(theme_name)


def run_tui(
    client: NetBoxApiClient,
    index: SchemaIndex,
    theme_name: str | None = None,
    demo_mode: bool = False,
) -> None:
    NetBoxTuiApp(
        client=client, index=index, theme_name=theme_name, demo_mode=demo_mode
    ).run()
