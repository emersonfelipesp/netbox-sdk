"""Developer Textual application for exploring and executing NetBox API operations."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from rich.style import Style
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Input,
    OptionList,
    Select,
    Static,
    TabbedContent,
    TabPane,
    TextArea,
    Tree,
)
from textual.widgets.option_list import Option

from netbox_cli.api import ApiResponse, ConnectionProbe, NetBoxApiClient
from netbox_cli.logging_runtime import get_logger
from netbox_cli.schema import Operation, SchemaIndex, parse_group_resource
from netbox_cli.theme_registry import ThemeDefinition

from .app import TOPBAR_CLI_LABEL
from .chrome import (
    SWITCH_TO_DEV_TUI,
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
from .dev_rendering import (
    completed_response_summary,
    operation_detail_text,
    operation_line_text,
    prepared_request_text,
    response_status_line,
    sending_status_line,
)
from .dev_state import (
    DevTuiState,
    DevViewState,
    RequestExecution,
    load_dev_tui_state,
    save_dev_tui_state,
)
from .formatting import humanize_group, humanize_resource
from .navigation import build_navigation_menus
from .plugin_discovery import discover_plugin_resource_paths
from .widgets import NbxButton, SupportModal

_HTTP_METHOD_OPTIONS = tuple(
    (method, method) for method in ("GET", "POST", "PUT", "PATCH", "DELETE")
)
_VIEW_MODE_OPTIONS = (
    ("- TUI", "main"),
    ("- Dev", "dev"),
)
logger = get_logger(__name__)


def _text_area_syntax_theme_for(catalog_theme: str) -> str:
    """Keep TextArea colors bound to the active app theme.

    Builtin TextArea themes ship their own palette, which drifts away from the
    repo's JSON theme tokens. Use the CSS-driven theme so editor chrome stays
    aligned with the selected app theme, then style component classes in TCSS.
    """
    del catalog_theme
    return "css"


class DevResponseReceived(Message):
    def __init__(self, response: ApiResponse, execution: RequestExecution) -> None:
        super().__init__()
        self.response = response
        self.execution = execution


class NetBoxDevTuiApp(App[None]):
    TITLE = "NetBox CLI Dev"
    SUB_TITLE = "Request workbench for API development"
    CSS_PATH = [
        str(Path(__file__).resolve().parent.parent / "ui_common.tcss"),
        str(Path(__file__).resolve().parent.parent / "dev_tui.tcss"),
    ]

    BINDINGS = [
        Binding("ctrl+enter", "send_request", "Send", priority=True),
        Binding("q", "quit", "Quit", priority=True),
        Binding("/", "focus_path", "Path", priority=True),
        Binding("g", "focus_navigation", "Navigation", priority=True),
        Binding("o", "focus_operations", "Operations", priority=True),
        Binding("b", "focus_body", "Body", priority=True),
    ]

    current_group = reactive[str | None](None)
    current_resource = reactive[str | None](None)

    def __init__(
        self,
        client: NetBoxApiClient,
        index: SchemaIndex,
        theme_name: str | None = None,
    ) -> None:
        super().__init__()
        self.client = client
        self.index = index
        # Plugin resources must come from the connected instance, not the bundled schema.
        self.index.remove_group_resources("plugins")
        self._state_scope = self.client.config.base_url
        self.state: DevTuiState = load_dev_tui_state(self._state_scope)
        self.theme_catalog, self.theme_name, self.theme_options = initialize_theme_state(
            self,
            requested_theme_name=theme_name,
            persisted_theme_name=self.state.theme_name,
        )

        self._clock_timer: Timer | None = None
        self._connection_timer: Timer | None = None
        self._last_connection_probe: ConnectionProbe | None = None
        self._resource_operations: list[Operation] = []
        self._visible_operations: list[Operation] = []
        if (
            self.state.last_view.group
            and self.state.last_view.resource
            and self.state.last_view.resource
            not in self.index.resources(self.state.last_view.group)
        ):
            self.state.last_view.group = None
            self.state.last_view.resource = None
            self.state.last_view.path = ""

    def compose(self) -> ComposeResult:
        ta_syntax = _text_area_syntax_theme_for(self.theme_name)
        with Horizontal(id="dev_topbar"):
            with Horizontal(id="dev_topbar_left"):
                yield Static("●", id="dev_nav_dot")
                yield Select(
                    options=self.theme_options,
                    value=self.theme_name,
                    prompt="Theme",
                    id="dev_theme_select",
                )
                yield Select(
                    options=_VIEW_MODE_OPTIONS,
                    value="dev",
                    prompt="View",
                    id="dev_view_select",
                )
            with Horizontal(id="dev_topbar_center"):
                yield Static(self._logo_renderable(), id="dev_logo")
                yield Static(TOPBAR_CLI_LABEL, id="dev_topbar_cli_suffix")
            with Horizontal(id="dev_topbar_right"):
                yield Static("", id="dev_clock")
                yield Static("●", id="dev_connection_badge", classes="-checking")
                yield Static("Context: <none>", id="dev_context_line")
                yield NbxButton(
                    "Liked it? Support me!",
                    id="support_button",
                    size="small",
                    tone="muted",
                    classes="nbx-topbar-control",
                )
                yield NbxButton(
                    "Close",
                    id="dev_close_button",
                    size="small",
                    tone="error",
                    classes="nbx-topbar-control",
                )

        with Horizontal(id="dev_request_bar"):
            yield Select(
                options=_HTTP_METHOD_OPTIONS,
                value=self.state.last_view.method or "GET",
                prompt="Method",
                id="dev_method_select",
            )
            yield Input(
                value=self.state.last_view.path,
                placeholder="/api/dcim/devices/",
                id="dev_path_input",
            )
            yield NbxButton(
                "Send",
                id="dev_send_button",
                size="medium",
                tone="primary",
                chrome="soft",
            )

        with Horizontal(id="dev_shell"):
            with Vertical(id="dev_sidebar"):
                yield Static("Resources", id="dev_sidebar_title")
                yield Tree("NetBox", id="dev_nav_tree")
                yield Static("g nav | o ops | / path | ctrl+enter send", id="dev_help")

            with Vertical(id="dev_main"):
                yield Static("No resource selected", id="dev_context")
                with Horizontal(id="dev_columns"):
                    with Vertical(id="dev_request_panel"):
                        with TabbedContent(id="dev_request_tabs"):
                            with TabPane("Operations", id="dev_operations_tab"):
                                yield Input(
                                    value="",
                                    placeholder="Search operations",
                                    id="dev_operation_search",
                                )
                                yield OptionList(id="dev_operation_list")
                                yield Static("", id="dev_operation_summary")
                            with TabPane("Query", id="dev_query_tab"):
                                yield Input(
                                    value=self.state.last_view.query_text,
                                    placeholder="key=value, limit=50",
                                    id="dev_query_input",
                                )
                                yield Static(
                                    "Relative path is sent via current NetBoxApiClient. Query values are comma-separated key=value pairs.",
                                    id="dev_query_help",
                                )
                            with TabPane("Body", id="dev_body_tab"):
                                yield TextArea.code_editor(
                                    self.state.last_view.body_text,
                                    language="json",
                                    soft_wrap=True,
                                    show_line_numbers=False,
                                    theme=ta_syntax,
                                    id="dev_body_editor",
                                )
                                yield Static(
                                    "JSON body is only sent for POST, PUT, and PATCH.",
                                    id="dev_body_help",
                                )
                    with Vertical(id="dev_response_panel"):
                        with Horizontal(id="dev_response_meta"):
                            yield Static("Idle", id="dev_response_status")
                            yield Static("-", id="dev_response_timing")
                            yield Static("-", id="dev_response_size")
                        with TabbedContent(id="dev_response_tabs"):
                            with TabPane("Body", id="dev_response_body_tab"):
                                yield TextArea.code_editor(
                                    "",
                                    language="json",
                                    soft_wrap=True,
                                    read_only=True,
                                    show_line_numbers=False,
                                    theme=ta_syntax,
                                    id="dev_response_body",
                                )
                            with TabPane("Headers", id="dev_response_headers_tab"):
                                yield TextArea.code_editor(
                                    "",
                                    language="yaml",
                                    soft_wrap=True,
                                    read_only=True,
                                    show_line_numbers=False,
                                    theme=ta_syntax,
                                    id="dev_response_headers",
                                )
                            with TabPane("Summary", id="dev_response_summary_tab"):
                                yield Static(
                                    "Choose a resource, review the request, then send it.",
                                    id="dev_response_summary",
                                )
        yield Footer()

    def _handle_exception(self, error: Exception) -> None:
        self._return_code = 1
        if self._exception is None:
            self._exception = error
            self._exception_event.set()
        detail = str(error).strip() or error.__class__.__name__
        theme = self._theme_definition()
        message = Text()
        message.append("Application error\n", style=Style(color=theme.colors["error"], bold=True))
        message.append(f"{detail}\n")
        message.append("The dev TUI closed to keep the terminal usable.")
        self.panic(message)

    def on_mount(self) -> None:
        logger.info("dev tui mounted")
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        self._build_navigation_tree()
        self._restore_last_view()
        self._update_clock()
        self._set_connection_badge_checking()
        self._probe_connection_health()
        self._discover_plugin_resources()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_dev_clock")
        self._connection_timer = self.set_interval(
            30.0, self._probe_connection_health, name="nbx_dev_connection"
        )
        self.query_one("#dev_nav_tree", Tree).focus()

    def on_unmount(self) -> None:
        logger.info("dev tui unmounting")
        if self._clock_timer is not None:
            self._clock_timer.stop()
            self._clock_timer = None
        if self._connection_timer is not None:
            self._connection_timer.stop()
            self._connection_timer = None
        method = self.state.last_view.method
        path = self.state.last_view.path
        query_text = self.state.last_view.query_text
        body_text = self.state.last_view.body_text
        try:
            method = str(self.query_one("#dev_method_select", Select).value or "GET")
            path = self.query_one("#dev_path_input", Input).value.strip()
            query_text = self.query_one("#dev_query_input", Input).value.strip()
            body_text = self.query_one("#dev_body_editor", TextArea).text
        except NoMatches:
            pass
        self.state.last_view = DevViewState(
            group=self.current_group,
            resource=self.current_resource,
            method=method,
            path=path,
            query_text=query_text,
            body_text=body_text,
        )
        self.state.theme_name = self.theme_name
        save_dev_tui_state(self.state, self._state_scope)

    def action_send_request(self) -> None:
        self.send_request_via_worker()

    def action_focus_path(self) -> None:
        self.query_one("#dev_path_input", Input).focus()

    def action_focus_navigation(self) -> None:
        self.query_one("#dev_nav_tree", Tree).focus()

    def action_focus_operations(self) -> None:
        self.query_one("#dev_operation_list", OptionList).focus()

    def action_focus_body(self) -> None:
        self.query_one("#dev_request_tabs", TabbedContent).active = "dev_body_tab"
        self.query_one("#dev_body_editor", TextArea).focus()

    @on(Button.Pressed, "#dev_close_button")
    def on_close_button_pressed(self) -> None:
        self.exit()

    @on(Button.Pressed, "#support_button")
    def on_support_button_pressed(self) -> None:
        self.push_screen(SupportModal())

    @on(Select.Changed, "#dev_view_select")
    def on_view_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        if str(event.value) == "main":
            self.exit(result=SWITCH_TO_MAIN_TUI)

    @on(Button.Pressed, "#dev_send_button")
    def on_send_button_pressed(self) -> None:
        self.send_request_via_worker()

    @on(Input.Submitted, "#dev_path_input")
    def on_path_submitted(self) -> None:
        self.send_request_via_worker()

    @on(Input.Changed, "#dev_operation_search")
    def on_operation_search_changed(self) -> None:
        self._refresh_operation_list()

    @on(OptionList.OptionSelected, "#dev_operation_list")
    def on_operation_selected(self, event: OptionList.OptionSelected) -> None:
        option_index = getattr(event, "option_index", getattr(event, "index", -1))
        if option_index < 0 or option_index >= len(self._visible_operations):
            return
        self._apply_operation(self._visible_operations[option_index])

    @on(Tree.NodeSelected, "#dev_nav_tree")
    def on_nav_selected(self, event: Tree.NodeSelected[tuple[str, str] | None]) -> None:
        if event.node.data is None:
            return
        group, resource = event.node.data
        self._activate_resource(group, resource)

    @on(Select.Changed, "#dev_theme_select")
    def on_theme_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = self.theme_catalog.resolve(str(event.value))
        if not selected or selected == self.theme_name:
            return
        self._apply_theme(selected, notify=True)
        self.call_after_refresh(self._strip_theme_select_prefix)

    @on(Select.Changed, "#dev_method_select")
    def on_method_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        self._set_response_summary(
            f"Request prepared: {event.value} {self.query_one('#dev_path_input', Input).value.strip() or '<path required>'}"
        )

    def watch_current_group(self, current_group: str | None) -> None:
        del current_group
        self._refresh_context()

    def watch_current_resource(self, current_resource: str | None) -> None:
        del current_resource
        self._refresh_context()

    def _refresh_context(self) -> None:
        target = self.query_one("#dev_context", Static)
        topbar_target = self.query_one("#dev_context_line", Static)
        if self.current_group and self.current_resource:
            context = (
                f"{humanize_group(self.current_group)} / {humanize_resource(self.current_resource)}"
            )
            target.update(context)
            topbar_target.update(f"Context: {context}")
        else:
            target.update("No resource selected")
            topbar_target.update("Context: <none>")

    def _build_navigation_tree(self) -> None:
        tree = self.query_one("#dev_nav_tree", Tree)
        tree.clear()
        root = tree.root
        root.expand()
        for menu in build_navigation_menus(self.index):
            menu_node = root.add(menu.label)
            for group in menu.groups:
                group_node = menu_node.add(group.label)
                for item in group.items:
                    data = (item.group, item.resource) if item.group and item.resource else None
                    group_node.add_leaf(item.label, data=data)

    def _restore_last_view(self) -> None:
        last_view = self.state.last_view
        if last_view.group and last_view.resource:
            if self.index.resource_paths(last_view.group, last_view.resource) is not None:
                self._activate_resource(last_view.group, last_view.resource)
                return
        self._set_response_summary(
            "Choose a resource from the left sidebar to load its operations."
        )

    def _activate_resource(self, group: str, resource: str) -> None:
        logger.info("dev tui selected resource %s/%s", group, resource)
        self.current_group = group
        self.current_resource = resource
        self._resource_operations = self.index.operations_for(group, resource)
        self.query_one("#dev_operation_search", Input).value = ""
        self._refresh_operation_list()
        default_operation = self._default_operation_for(group, resource)
        if default_operation is not None:
            self._apply_operation(default_operation)
        else:
            self.query_one("#dev_method_select", Select).value = "GET"
            path = f"/api/{group}/{resource}/"
            self.query_one("#dev_path_input", Input).value = path
            self._set_operation_summary("No OpenAPI operation metadata found.")
            self._set_response_summary(f"Prepared GET {path}")

    @work(group="plugin_discovery", exclusive=True, thread=False)
    async def _discover_plugin_resources(self) -> None:
        changed = False
        for list_path, detail_path in await discover_plugin_resource_paths(self.client):
            group, resource = parse_group_resource(list_path)
            if group != "plugins" or resource is None:
                continue
            changed = (
                self.index.add_discovered_resource(
                    group=group,
                    resource=resource,
                    list_path=list_path,
                    detail_path=detail_path,
                )
                or changed
            )
        if not changed:
            return
        self._build_navigation_tree()
        if self.current_group is None and self.current_resource is None:
            self._restore_last_view()

    def _default_operation_for(self, group: str, resource: str) -> Operation | None:
        paths = self.index.resource_paths(group, resource)
        preferred_path = paths.list_path if paths is not None else None
        for operation in self._resource_operations:
            if operation.method == "GET" and operation.path == preferred_path:
                return operation
        return self._resource_operations[0] if self._resource_operations else None

    def _refresh_operation_list(self, highlight_index: int | None = None) -> None:
        search = self.query_one("#dev_operation_search", Input).value.strip().lower()
        operations = [
            operation
            for operation in self._resource_operations
            if not search
            or search in operation.method.lower()
            or search in operation.path.lower()
            or search in operation.summary.lower()
            or search in operation.operation_id.lower()
        ]
        self._visible_operations = operations
        option_list = self.query_one("#dev_operation_list", OptionList)
        if not self._visible_operations:
            option_list.set_options(["No matching operations"])
            option_list.highlighted = None
            return
        theme = self._theme_definition()
        option_list.set_options(
            [
                Option(operation_line_text(theme, operation.method, operation.path))
                for operation in self._visible_operations
            ]
        )
        if highlight_index is None:
            option_list.highlighted = 0
        else:
            option_list.highlighted = min(highlight_index, len(self._visible_operations) - 1)

    def _apply_operation(self, operation: Operation) -> None:
        self.query_one("#dev_method_select", Select).value = operation.method
        self.query_one("#dev_path_input", Input).value = operation.path
        theme = self._theme_definition()
        summary = operation.summary or operation.operation_id or "No summary available."
        self._set_operation_summary(operation_detail_text(theme, operation, summary))
        self.query_one("#dev_request_tabs", TabbedContent).active = "dev_operations_tab"
        self._set_response_summary(prepared_request_text(theme, operation.method, operation.path))

    def _set_operation_summary(self, content: Text | str) -> None:
        self.query_one("#dev_operation_summary", Static).update(content)

    def _set_response_summary(self, content: Text | str) -> None:
        self.query_one("#dev_response_summary", Static).update(content)

    def _theme_definition(self) -> ThemeDefinition:
        return self.theme_catalog.theme_for(self.theme_name)

    def _parse_query_text(self, raw: str) -> dict[str, str]:
        raw = raw.strip()
        if not raw:
            return {}
        pairs: dict[str, str] = {}
        for chunk in [part.strip() for part in raw.split(",") if part.strip()]:
            if "=" not in chunk:
                raise ValueError(f"Expected key=value query entry, got: {chunk}")
            key, value = chunk.split("=", 1)
            key = key.strip()
            if not key:
                raise ValueError(f"Expected key=value query entry, got: {chunk}")
            pairs[key] = value.strip()
        return pairs

    def _build_payload(self, method: str) -> dict[str, Any] | list[Any] | None:
        if method not in {"POST", "PUT", "PATCH"}:
            return None
        raw = self.query_one("#dev_body_editor", TextArea).text.strip()
        if not raw:
            return None
        payload = json.loads(raw)
        if not isinstance(payload, (dict, list)):
            raise ValueError("JSON body must decode to an object or array.")
        return payload

    @work(group="dev_request", exclusive=True, thread=False)
    async def send_request_via_worker(self) -> None:
        try:
            method = str(self.query_one("#dev_method_select", Select).value or "GET")
            path = self.query_one("#dev_path_input", Input).value.strip()
            if not path:
                raise ValueError("Request path cannot be empty.")
            query = self._parse_query_text(self.query_one("#dev_query_input", Input).value.strip())
            payload = self._build_payload(method)
        except Exception as exc:  # noqa: BLE001
            self._set_request_error(str(exc).strip() or exc.__class__.__name__)
            return

        self._set_request_in_flight(method, path)
        logger.info("dev tui sending %s %s", method, path)
        started = perf_counter()
        try:
            response = await self.client.request(
                method,
                path,
                query=query,
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("dev tui request failed for %s %s", method, path)
            self._set_request_error(str(exc).strip() or exc.__class__.__name__)
            return

        execution = RequestExecution(
            method=method,
            path=path,
            query=query,
            payload=payload,
            duration_ms=(perf_counter() - started) * 1000,
        )
        self.post_message(DevResponseReceived(response, execution))

    @on(DevResponseReceived)
    def on_response_received(self, event: DevResponseReceived) -> None:
        response = event.response
        execution = event.execution
        self._render_response(response, execution)

    def _set_request_in_flight(self, method: str, path: str) -> None:
        theme = self._theme_definition()
        self.query_one("#dev_response_status", Static).update(
            sending_status_line(theme, method, path)
        )
        self.query_one("#dev_response_timing", Static).update("...")
        self.query_one("#dev_response_size", Static).update("...")
        self._set_response_summary(
            Text(
                "Request in flight via the current NetBoxApiClient implementation.",
                style=Style(color=theme.variables["nb-muted-text"]),
            )
        )

    def _set_request_error(self, message: str) -> None:
        self.query_one("#dev_response_status", Static).update(
            Text("Request failed", style=f"bold {self._theme_definition().colors['error']}")
        )
        self.query_one("#dev_response_timing", Static).update("-")
        self.query_one("#dev_response_size", Static).update("-")
        self.query_one("#dev_response_body", TextArea).text = message
        self.query_one("#dev_response_headers", TextArea).text = ""
        self._set_response_summary(message)
        self.notify(message, severity="error")

    def _render_response(self, response: ApiResponse, execution: RequestExecution) -> None:
        theme = self._theme_definition()
        self.query_one("#dev_response_status", Static).update(
            response_status_line(theme, response.status)
        )
        self.query_one("#dev_response_timing", Static).update(f"{execution.duration_ms:.1f} ms")
        self.query_one("#dev_response_size", Static).update(
            f"{len(response.text.encode('utf-8'))} B"
        )
        self.query_one("#dev_response_body", TextArea).text = self._format_response_body(response)
        self.query_one("#dev_response_headers", TextArea).text = self._format_headers(
            response.headers
        )
        self._set_response_summary(completed_response_summary(theme, execution, response))
        self.query_one("#dev_response_tabs", TabbedContent).active = "dev_response_body_tab"

    def _format_response_body(self, response: ApiResponse) -> str:
        content_type = response.headers.get("Content-Type", "")
        if "json" in content_type.lower():
            try:
                return json.dumps(json.loads(response.text), indent=2, sort_keys=True)
            except json.JSONDecodeError:
                return response.text
        try:
            return json.dumps(json.loads(response.text), indent=2, sort_keys=True)
        except json.JSONDecodeError:
            return response.text

    def _format_headers(self, headers: dict[str, str]) -> str:
        if not headers:
            return ""
        return "\n".join(f"{key}: {value}" for key, value in sorted(headers.items()))

    @work(group="dev_connection_probe", exclusive=True, thread=False)
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

    def _update_clock(self) -> None:
        update_clock_widget(self, widget_id="#dev_clock")

    def _set_connection_badge_checking(self) -> None:
        set_connection_badge_state(self, badge_id="#dev_connection_badge", state="checking")

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        set_connection_badge_state(
            self,
            badge_id="#dev_connection_badge",
            state=badge_state_for_probe(probe),
        )

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        self.theme_name = apply_theme(
            self,
            theme_catalog=self.theme_catalog,
            theme_options=self.theme_options,
            current_theme_name=self.theme_name,
            new_theme_name=theme_name,
            state=self.state,
            logo_widget_id="#dev_logo",
            notify=notify,
        )
        self._sync_text_area_syntax_themes()
        if self.current_group and self.current_resource:
            try:
                prev_hl = self.query_one("#dev_operation_list", OptionList).highlighted
            except NoMatches:
                prev_hl = None
            self._refresh_operation_list(highlight_index=prev_hl)
            if self._visible_operations:
                idx = min(prev_hl, len(self._visible_operations) - 1) if prev_hl is not None else 0
                op = self._visible_operations[idx]
                summary = op.summary or op.operation_id or "No summary available."
                self._set_operation_summary(
                    operation_detail_text(self._theme_definition(), op, summary)
                )

    def _logo_renderable(self):
        return logo_renderable(self.theme_catalog, self.theme_name)

    def _sync_text_area_syntax_themes(self) -> None:
        """Keep TextArea syntax themes aligned with the catalog theme selection."""
        ta_theme = _text_area_syntax_theme_for(self.theme_name)
        for widget in self.query(TextArea):
            widget.theme = ta_theme

    def _strip_theme_select_prefix(self) -> None:
        strip_theme_select_prefix(self, selector="#dev_theme_select SelectCurrent Static#label")
        strip_theme_select_prefix(self, selector="#dev_view_select SelectCurrent Static#label")


def available_theme_names() -> tuple[str, ...]:
    return get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return get_theme_catalog().resolve(theme_name)


def run_dev_tui(
    client: NetBoxApiClient,
    index: SchemaIndex,
    theme_name: str | None = None,
    demo_mode: bool = False,
) -> None:
    try:
        next_mode = "dev"
        next_theme = theme_name
        while True:
            if next_mode == "dev":
                app = NetBoxDevTuiApp(client=client, index=index, theme_name=next_theme)
                result = app.run()
                if result == SWITCH_TO_MAIN_TUI:
                    next_mode = "main"
                    next_theme = app.theme_name
                    continue
                return

            from .app import NetBoxTuiApp

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
            return
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        raise RuntimeError(f"Unable to launch the dev TUI: {detail}") from None
