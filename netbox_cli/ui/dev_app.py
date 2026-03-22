from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

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

from netbox_cli.api import ApiResponse, ConnectionProbe, NetBoxApiClient
from netbox_cli.schema import Operation, SchemaIndex
from netbox_cli.theme_registry import ThemeCatalog, ThemeDefinition, load_theme_catalog

from .dev_state import DevTuiState, DevViewState, load_dev_tui_state, save_dev_tui_state
from .formatting import configure_semantic_styles, humanize_group, humanize_resource
from .logo_render import build_netbox_logo
from .navigation import build_navigation_menus

_THEME_CATALOG: ThemeCatalog | None = None
_HTTP_METHOD_OPTIONS = tuple(
    (method, method) for method in ("GET", "POST", "PUT", "PATCH", "DELETE")
)


def _get_theme_catalog() -> ThemeCatalog:
    global _THEME_CATALOG
    if _THEME_CATALOG is None:
        _THEME_CATALOG = load_theme_catalog()
    return _THEME_CATALOG


@dataclass(slots=True)
class RequestExecution:
    method: str
    path: str
    query: dict[str, str]
    payload: dict[str, Any] | list[Any] | None
    duration_ms: float


class DevResponseReceived(Message):
    def __init__(self, response: ApiResponse, execution: RequestExecution) -> None:
        super().__init__()
        self.response = response
        self.execution = execution


class NetBoxDevTuiApp(App[None]):
    TITLE = "NetBox CLI Dev"
    SUB_TITLE = "Request workbench for API development"
    CSS_PATH = str(Path(__file__).resolve().parent.parent / "dev_tui.tcss")

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
        self.state: DevTuiState = load_dev_tui_state()
        self.theme_catalog = _get_theme_catalog()
        requested_theme = self.theme_catalog.resolve(theme_name) if theme_name is not None else None
        state_theme = self.theme_catalog.resolve(self.state.theme_name)
        self.theme_name = requested_theme or state_theme or self.theme_catalog.default_theme_name
        self.theme_options = self.theme_catalog.select_options()
        active_definition = self.theme_catalog.theme_for(self.theme_name)
        configure_semantic_styles(
            colors=active_definition.colors,
            variables=active_definition.variables,
        )
        for definition in self.theme_catalog.themes:
            self.register_theme(definition.to_textual_theme())
        self.theme = self.theme_name

        self._clock_timer: Timer | None = None
        self._connection_timer: Timer | None = None
        self._last_connection_probe: ConnectionProbe | None = None
        self._resource_operations: list[Operation] = []
        self._visible_operations: list[Operation] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="dev_topbar"):
            with Horizontal(id="dev_topbar_left"):
                yield Static("●", id="dev_nav_dot")
                yield Select(
                    options=self.theme_options,
                    value=self.theme_name,
                    prompt="Theme",
                    id="dev_theme_select",
                )
                yield Static(self.TITLE, id="dev_title")
                yield Static("Workbench", id="dev_title_suffix")
            with Horizontal(id="dev_topbar_center"):
                yield Static(self._logo_renderable(), id="dev_logo")
            with Horizontal(id="dev_topbar_right"):
                yield Static("", id="dev_clock")
                yield Static("●", id="dev_connection_badge", classes="-checking")
                yield Button("Close", id="dev_close_button")

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
            yield Button("Send", id="dev_send_button", variant="primary")

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
                                    id="dev_response_body",
                                )
                            with TabPane("Headers", id="dev_response_headers_tab"):
                                yield TextArea.code_editor(
                                    "",
                                    language="yaml",
                                    soft_wrap=True,
                                    read_only=True,
                                    show_line_numbers=False,
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
        self.panic(
            Text.from_markup(
                "[bold]Application error[/bold]\n"
                f"{detail}\n"
                "The dev TUI closed to keep the terminal usable."
            )
        )

    def on_mount(self) -> None:
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        self._build_navigation_tree()
        self._restore_last_view()
        self._update_clock()
        self._set_connection_badge_checking()
        self._probe_connection_health()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_dev_clock")
        self._connection_timer = self.set_interval(
            30.0, self._probe_connection_health, name="nbx_dev_connection"
        )
        self.query_one("#dev_nav_tree", Tree).focus()

    def on_unmount(self) -> None:
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
        save_dev_tui_state(self.state)

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
            if event.node.children:
                event.node.toggle()
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
        if self.current_group and self.current_resource:
            target.update(
                f"{humanize_group(self.current_group)} / {humanize_resource(self.current_resource)}"
            )
        else:
            target.update("No resource selected")

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

    def _default_operation_for(self, group: str, resource: str) -> Operation | None:
        paths = self.index.resource_paths(group, resource)
        preferred_path = paths.list_path if paths is not None else None
        for operation in self._resource_operations:
            if operation.method == "GET" and operation.path == preferred_path:
                return operation
        return self._resource_operations[0] if self._resource_operations else None

    def _refresh_operation_list(self) -> None:
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
        prompts = [f"{operation.method} {operation.path}" for operation in self._visible_operations]
        if not prompts:
            prompts = ["No matching operations"]
        option_list = self.query_one("#dev_operation_list", OptionList)
        option_list.set_options(prompts)
        option_list.highlighted = 0 if self._visible_operations else None

    def _apply_operation(self, operation: Operation) -> None:
        self.query_one("#dev_method_select", Select).value = operation.method
        self.query_one("#dev_path_input", Input).value = operation.path
        summary = operation.summary or operation.operation_id or "No summary available."
        self._set_operation_summary(f"{operation.method} {operation.path}\n{summary}")
        self.query_one("#dev_request_tabs", TabbedContent).active = "dev_operations_tab"
        self._set_response_summary(f"Prepared {operation.method} {operation.path}")

    def _set_operation_summary(self, text: str) -> None:
        self.query_one("#dev_operation_summary", Static).update(text)

    def _set_response_summary(self, text: str) -> None:
        self.query_one("#dev_response_summary", Static).update(text)

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
        started = perf_counter()
        try:
            response = await self.client.request(
                method,
                path,
                query=query,
                payload=payload,
            )
        except Exception as exc:  # noqa: BLE001
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
        self.query_one("#dev_response_status", Static).update(f"Sending {method} {path}")
        self.query_one("#dev_response_timing", Static).update("...")
        self.query_one("#dev_response_size", Static).update("...")
        self._set_response_summary(
            "Request in flight via the current NetBoxApiClient implementation."
        )

    def _set_request_error(self, message: str) -> None:
        self.query_one("#dev_response_status", Static).update("Request failed")
        self.query_one("#dev_response_timing", Static).update("-")
        self.query_one("#dev_response_size", Static).update("-")
        self.query_one("#dev_response_body", TextArea).text = message
        self.query_one("#dev_response_headers", TextArea).text = ""
        self._set_response_summary(message)
        self.notify(message, severity="error")

    def _render_response(self, response: ApiResponse, execution: RequestExecution) -> None:
        status_text = f"HTTP {response.status}"
        self.query_one("#dev_response_status", Static).update(status_text)
        self.query_one("#dev_response_timing", Static).update(f"{execution.duration_ms:.1f} ms")
        self.query_one("#dev_response_size", Static).update(
            f"{len(response.text.encode('utf-8'))} B"
        )
        self.query_one("#dev_response_body", TextArea).text = self._format_response_body(response)
        self.query_one("#dev_response_headers", TextArea).text = self._format_headers(
            response.headers
        )
        query_text = "&".join(f"{key}={value}" for key, value in execution.query.items()) or "-"
        payload_text = (
            "none"
            if execution.payload is None
            else json.dumps(execution.payload, indent=2, sort_keys=True)
        )
        self._set_response_summary(
            f"{execution.method} {execution.path}\n"
            f"Query: {query_text}\n"
            f"Payload: {payload_text}\n"
            f"Status: {response.status}"
        )
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
        try:
            self.query_one("#dev_clock", Static).update(datetime.now().strftime("%H:%M:%S"))
        except NoMatches:
            pass

    def _set_connection_badge_checking(self) -> None:
        badge = self.query_one("#dev_connection_badge", Static)
        badge.remove_class("-ok")
        badge.remove_class("-warning")
        badge.remove_class("-error")
        badge.add_class("-checking")
        badge.update("●")

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        badge = self.query_one("#dev_connection_badge", Static)
        badge.remove_class("-checking")
        badge.remove_class("-ok")
        badge.remove_class("-warning")
        badge.remove_class("-error")
        if probe.status == 0:
            badge.add_class("-error")
            badge.update("●")
            return
        if probe.ok and probe.status < 300:
            badge.add_class("-ok")
            badge.update("●")
            return
        if probe.ok and probe.status == 403:
            badge.add_class("-warning")
            badge.update("●")
            return
        badge.add_class("-error")
        badge.update("●")

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        definition = self.theme_catalog.theme_for(theme_name)
        configure_semantic_styles(
            colors=definition.colors,
            variables=definition.variables,
        )
        previous = self.theme_name
        if previous:
            self.screen.remove_class(f"theme-{previous}")
        self.theme_name = theme_name
        self.state.theme_name = theme_name
        self.theme = theme_name
        self.screen.add_class(f"theme-{theme_name}")
        self._refresh_logo(definition)
        if notify:
            label = next(
                (name for name, key in self.theme_options if key == theme_name),
                theme_name,
            )
            self.notify(f"Theme switched to {label}")

    def _logo_renderable(self) -> Text:
        return build_netbox_logo(self.theme_catalog.theme_for(self.theme_name))

    def _refresh_logo(self, definition: ThemeDefinition) -> None:
        try:
            logo = self.query_one("#dev_logo", Static)
        except NoMatches:
            return
        logo.update(build_netbox_logo(definition))

    def _strip_theme_select_prefix(self) -> None:
        try:
            label = self.query_one("#dev_theme_select SelectCurrent Static#label", Static)
        except NoMatches:
            return
        text = str(label.content)
        if text.startswith("- "):
            label.update(text[2:])


def available_theme_names() -> tuple[str, ...]:
    return _get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return _get_theme_catalog().resolve(theme_name)


def run_dev_tui(
    client: NetBoxApiClient,
    index: SchemaIndex,
    theme_name: str | None = None,
) -> None:
    try:
        NetBoxDevTuiApp(client=client, index=index, theme_name=theme_name).run()
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        raise RuntimeError(f"Unable to launch the dev TUI: {detail}") from None
