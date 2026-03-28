"""GraphQL Textual application for exploring and executing NetBox GraphQL queries."""

from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
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
)
from textual.widgets.option_list import Option

from netbox_sdk.client import ApiResponse, ConnectionProbe, NetBoxApiClient
from netbox_sdk.logging_runtime import get_logger
from netbox_tui.app import TOPBAR_CLI_LABEL
from netbox_tui.chrome import (
    apply_theme,
    badge_state_for_probe,
    get_theme_catalog,
    initialize_theme_state,
    logo_renderable,
    set_connection_badge_state,
    strip_theme_select_prefix,
    update_clock_widget,
)
from netbox_tui.graphql_state import (
    GraphqlHistoryEntry,
    GraphqlTuiState,
    load_graphql_tui_state,
    save_graphql_tui_state,
)
from netbox_tui.theme_registry import ThemeDefinition
from netbox_tui.widgets import NbxButton, SupportModal

logger = get_logger(__name__)

_VIEW_MODE_OPTIONS = (("- GraphQL", "graphql"),)
_INTROSPECTION_QUERY = """
query NbxGraphqlIntrospection {
  __schema {
    queryType { name }
    types {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          name
          description
          defaultValue
          type {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
        type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                }
              }
            }
          }
        }
      }
      inputFields {
        name
        description
        defaultValue
        type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                }
              }
            }
          }
        }
      }
      enumValues(includeDeprecated: true) {
        name
        description
      }
      possibleTypes {
        kind
        name
      }
    }
  }
}
""".strip()


def _text_area_syntax_theme_for(catalog_theme: str) -> str:
    del catalog_theme
    return "css"


@dataclass(slots=True)
class TypeRef:
    kind: str
    name: str | None = None
    of_type: TypeRef | None = None


@dataclass(slots=True)
class GraphqlArgInfo:
    name: str
    type_ref: TypeRef
    default_value: str | None = None
    description: str | None = None


@dataclass(slots=True)
class GraphqlFieldInfo:
    name: str
    type_ref: TypeRef
    args: list[GraphqlArgInfo] = field(default_factory=list)
    description: str | None = None


@dataclass(slots=True)
class GraphqlInputFieldInfo:
    name: str
    type_ref: TypeRef
    default_value: str | None = None
    description: str | None = None


@dataclass(slots=True)
class GraphqlTypeInfo:
    name: str
    kind: str
    description: str | None = None
    fields: list[GraphqlFieldInfo] = field(default_factory=list)
    input_fields: list[GraphqlInputFieldInfo] = field(default_factory=list)
    enum_values: list[str] = field(default_factory=list)
    possible_types: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GraphqlExplorerModel:
    query_type_name: str
    types: dict[str, GraphqlTypeInfo]

    def root_fields(self) -> list[GraphqlFieldInfo]:
        query_type = self.types.get(self.query_type_name)
        return list(query_type.fields if query_type else [])

    def named_type_name(self, type_ref: TypeRef | None) -> str | None:
        current = type_ref
        while current is not None and current.kind in {"NON_NULL", "LIST"}:
            current = current.of_type
        return current.name if current is not None else None

    def named_type(self, type_ref: TypeRef | None) -> GraphqlTypeInfo | None:
        name = self.named_type_name(type_ref)
        return self.types.get(name) if name else None


@dataclass(slots=True)
class GraphqlExecution:
    query_text: str
    variables: dict[str, Any] | None
    duration_ms: float


class GraphqlSchemaLoaded(Message):
    def __init__(self, explorer: GraphqlExplorerModel | None, error: str | None = None) -> None:
        super().__init__()
        self.explorer = explorer
        self.error = error


class GraphqlResponseReceived(Message):
    def __init__(self, response: ApiResponse, execution: GraphqlExecution) -> None:
        super().__init__()
        self.response = response
        self.execution = execution


def _parse_type_ref(node: dict[str, Any] | None) -> TypeRef:
    if not isinstance(node, dict):
        return TypeRef(kind="SCALAR", name="String")
    return TypeRef(
        kind=str(node.get("kind") or "SCALAR"),
        name=node.get("name"),
        of_type=_parse_type_ref(node.get("ofType"))
        if isinstance(node.get("ofType"), dict)
        else None,
    )


def _type_label(type_ref: TypeRef | None) -> str:
    if type_ref is None:
        return "Unknown"
    if type_ref.kind == "NON_NULL":
        return f"{_type_label(type_ref.of_type)}!"
    if type_ref.kind == "LIST":
        return f"[{_type_label(type_ref.of_type)}]"
    return type_ref.name or type_ref.kind


def _parse_explorer(payload: dict[str, Any]) -> GraphqlExplorerModel:
    schema = payload.get("__schema")
    if not isinstance(schema, dict):
        raise ValueError("GraphQL introspection response did not include __schema.")
    query_type = schema.get("queryType")
    query_type_name = query_type.get("name") if isinstance(query_type, dict) else None
    if not isinstance(query_type_name, str) or not query_type_name:
        raise ValueError("GraphQL introspection response did not include queryType.name.")

    types: dict[str, GraphqlTypeInfo] = {}
    for type_node in schema.get("types", []):
        if not isinstance(type_node, dict):
            continue
        name = type_node.get("name")
        if not isinstance(name, str) or not name or name.startswith("__"):
            continue
        gql_type = GraphqlTypeInfo(
            name=name,
            kind=str(type_node.get("kind") or "UNKNOWN"),
            description=type_node.get("description"),
        )
        for field_node in type_node.get("fields", []) or []:
            if not isinstance(field_node, dict) or not isinstance(field_node.get("name"), str):
                continue
            gql_field = GraphqlFieldInfo(
                name=field_node["name"],
                type_ref=_parse_type_ref(field_node.get("type")),
                description=field_node.get("description"),
            )
            for arg_node in field_node.get("args", []) or []:
                if not isinstance(arg_node, dict) or not isinstance(arg_node.get("name"), str):
                    continue
                gql_field.args.append(
                    GraphqlArgInfo(
                        name=arg_node["name"],
                        type_ref=_parse_type_ref(arg_node.get("type")),
                        default_value=arg_node.get("defaultValue"),
                        description=arg_node.get("description"),
                    )
                )
            gql_type.fields.append(gql_field)
        for input_node in type_node.get("inputFields", []) or []:
            if not isinstance(input_node, dict) or not isinstance(input_node.get("name"), str):
                continue
            gql_type.input_fields.append(
                GraphqlInputFieldInfo(
                    name=input_node["name"],
                    type_ref=_parse_type_ref(input_node.get("type")),
                    default_value=input_node.get("defaultValue"),
                    description=input_node.get("description"),
                )
            )
        gql_type.enum_values = [
            value["name"]
            for value in type_node.get("enumValues", []) or []
            if isinstance(value, dict) and isinstance(value.get("name"), str)
        ]
        gql_type.possible_types = [
            value["name"]
            for value in type_node.get("possibleTypes", []) or []
            if isinstance(value, dict) and isinstance(value.get("name"), str)
        ]
        types[name] = gql_type

    return GraphqlExplorerModel(query_type_name=query_type_name, types=types)


class NetBoxGraphqlTuiApp(App[None]):
    TITLE = "NetBox SDK GraphQL"
    SUB_TITLE = "Interactive GraphQL explorer and query runner"
    CSS_PATH = [
        str(Path(__file__).resolve().parent / "ui_common.tcss"),
        str(Path(__file__).resolve().parent / "graphql_tui.tcss"),
    ]
    BINDINGS = [
        Binding("ctrl+enter", "send_query", "Run", priority=True),
        Binding("/", "focus_search", "Search", priority=True),
        Binding("e", "focus_query", "Query", priority=True),
        Binding("v", "focus_variables", "Variables", priority=True),
        Binding("q", "quit", "Quit", priority=True),
    ]

    selected_field_name = reactive[str | None](None)

    def __init__(self, client: NetBoxApiClient, theme_name: str | None = None) -> None:
        super().__init__()
        self.client = client
        self._state_scope = self.client.config.base_url
        self.state: GraphqlTuiState = load_graphql_tui_state(self._state_scope)
        self.theme_catalog, self.theme_name, self.theme_options = initialize_theme_state(
            self,
            requested_theme_name=theme_name,
            persisted_theme_name=self.state.theme_name,
        )
        self._clock_timer: Timer | None = None
        self._connection_timer: Timer | None = None
        self._last_connection_probe: ConnectionProbe | None = None
        self._explorer: GraphqlExplorerModel | None = None
        self._visible_root_fields: list[GraphqlFieldInfo] = []

    def compose(self) -> ComposeResult:
        ta_theme = _text_area_syntax_theme_for(self.theme_name)
        with Horizontal(id="graphql_topbar"):
            with Horizontal(id="graphql_topbar_left"):
                yield Static("●", id="graphql_nav_dot")
                yield Select(
                    options=self.theme_options,
                    value=self.theme_name,
                    prompt="Theme",
                    id="graphql_theme_select",
                )
                yield Select(
                    options=_VIEW_MODE_OPTIONS,
                    value="graphql",
                    prompt="View",
                    id="graphql_view_select",
                )
            with Horizontal(id="graphql_topbar_center"):
                yield Static(self._logo_renderable(), id="graphql_logo")
                yield Static(TOPBAR_CLI_LABEL, id="graphql_topbar_cli_suffix")
            with Horizontal(id="graphql_topbar_right"):
                yield Static("", id="graphql_clock")
                yield Static("●", id="graphql_connection_badge", classes="-checking")
                yield Static("Field: <none>", id="graphql_context_line")
                yield NbxButton(
                    "Liked it? Support me!",
                    id="support_button",
                    size="small",
                    tone="muted",
                    classes="nbx-topbar-control",
                )
                yield NbxButton(
                    "Close",
                    id="graphql_close_button",
                    size="small",
                    tone="error",
                    classes="nbx-topbar-control",
                )

        with Horizontal(id="graphql_shell"):
            with Vertical(id="graphql_sidebar"):
                yield Static("Root Query Fields", id="graphql_sidebar_title")
                yield Input(
                    value="",
                    placeholder="Search root fields",
                    id="graphql_field_search",
                )
                yield OptionList(id="graphql_field_list")
                with TabbedContent(id="graphql_sidebar_tabs"):
                    with TabPane("Details", id="graphql_details_tab"):
                        yield Static(
                            "Loading GraphQL schema introspection from the connected NetBox instance.",
                            id="graphql_field_details",
                        )
                    with TabPane("History", id="graphql_history_tab"):
                        yield OptionList(id="graphql_history_list")
                yield Static(
                    "/ search | e query | v variables | ctrl+enter run",
                    id="graphql_help",
                )

            with Vertical(id="graphql_builder_panel"):
                with Horizontal(id="graphql_action_bar"):
                    yield NbxButton(
                        "Build Field", id="graphql_build_field_button", size="small", tone="primary"
                    )
                    yield NbxButton(
                        "Insert Args", id="graphql_insert_args_button", size="small", tone="muted"
                    )
                    yield NbxButton(
                        "Insert Filters",
                        id="graphql_insert_filters_button",
                        size="small",
                        tone="muted",
                    )
                    yield NbxButton(
                        "Insert Pagination",
                        id="graphql_insert_pagination_button",
                        size="small",
                        tone="muted",
                    )
                    yield NbxButton(
                        "Insert Fragments",
                        id="graphql_insert_fragments_button",
                        size="small",
                        tone="muted",
                    )
                    yield NbxButton("Run", id="graphql_send_button", size="small", tone="primary")
                with TabbedContent(id="graphql_request_tabs"):
                    with TabPane("Query", id="graphql_query_tab"):
                        yield TextArea.code_editor(
                            self.state.last_query_text,
                            soft_wrap=True,
                            show_line_numbers=False,
                            theme=ta_theme,
                            id="graphql_query_editor",
                        )
                    with TabPane("Variables", id="graphql_variables_tab"):
                        yield TextArea.code_editor(
                            self.state.last_variables_text,
                            language="json",
                            soft_wrap=True,
                            show_line_numbers=False,
                            theme=ta_theme,
                            id="graphql_variables_editor",
                        )
                        yield Static(
                            "Variables must be a JSON object. Leave blank when unused.",
                            id="graphql_variables_help",
                        )

            with Vertical(id="graphql_response_panel"):
                with Horizontal(id="graphql_response_meta"):
                    yield Static("Idle", id="graphql_response_status")
                    yield Static("-", id="graphql_response_timing")
                    yield Static("-", id="graphql_response_size")
                    yield NbxButton(
                        "Copy",
                        id="graphql_copy_response_button",
                        size="small",
                        tone="muted",
                        disabled=True,
                    )
                with TabbedContent(id="graphql_response_tabs"):
                    with TabPane("Body", id="graphql_response_body_tab"):
                        yield TextArea.code_editor(
                            "",
                            language="json",
                            soft_wrap=True,
                            read_only=True,
                            show_line_numbers=False,
                            theme=ta_theme,
                            id="graphql_response_body",
                        )
                    with TabPane("Headers", id="graphql_response_headers_tab"):
                        yield TextArea.code_editor(
                            "",
                            language="yaml",
                            soft_wrap=True,
                            read_only=True,
                            show_line_numbers=False,
                            theme=ta_theme,
                            id="graphql_response_headers",
                        )
                    with TabPane("Summary", id="graphql_response_summary_tab"):
                        yield Static(
                            "Query builder ready. Select a root field or type a GraphQL query directly.",
                            id="graphql_response_summary",
                        )
        yield Footer()

    def on_mount(self) -> None:
        logger.info("graphql tui mounted")
        self._apply_theme(self.theme_name)
        self.call_after_refresh(self._strip_theme_select_prefix)
        self._render_history()
        self._update_clock()
        self._set_connection_badge_checking()
        self._probe_connection_health()
        self._load_schema()
        self._clock_timer = self.set_interval(1.0, self._update_clock, name="nbx_graphql_clock")
        self._connection_timer = self.set_interval(
            30.0, self._probe_connection_health, name="nbx_graphql_connection"
        )
        self.query_one("#graphql_field_search", Input).focus()

    def on_unmount(self) -> None:
        logger.info("graphql tui unmounting")
        if self._clock_timer is not None:
            self._clock_timer.stop()
        if self._connection_timer is not None:
            self._connection_timer.stop()
        try:
            self.state.last_query_text = self.query_one("#graphql_query_editor", TextArea).text
            self.state.last_variables_text = self.query_one(
                "#graphql_variables_editor", TextArea
            ).text
        except NoMatches:
            pass
        self.state.selected_root_field = self.selected_field_name
        self.state.theme_name = self.theme_name
        save_graphql_tui_state(self.state, self._state_scope)

    def action_send_query(self) -> None:
        self.send_query_via_worker()

    def action_focus_search(self) -> None:
        self.query_one("#graphql_field_search", Input).focus()

    def action_focus_query(self) -> None:
        self.query_one("#graphql_request_tabs", TabbedContent).active = "graphql_query_tab"
        self.query_one("#graphql_query_editor", TextArea).focus()

    def action_focus_variables(self) -> None:
        self.query_one("#graphql_request_tabs", TabbedContent).active = "graphql_variables_tab"
        self.query_one("#graphql_variables_editor", TextArea).focus()

    @on(Button.Pressed, "#graphql_close_button")
    def on_close_button_pressed(self) -> None:
        self.exit()

    @on(Button.Pressed, "#support_button")
    def on_support_button_pressed(self) -> None:
        self.push_screen(SupportModal())

    @on(Select.Changed, "#graphql_theme_select")
    def on_theme_changed(self, event: Select.Changed) -> None:
        if event.value == Select.BLANK:
            return
        selected = self.theme_catalog.resolve(str(event.value))
        if not selected or selected == self.theme_name:
            return
        self._apply_theme(selected, notify=True)
        self.call_after_refresh(self._strip_theme_select_prefix)

    @on(OptionList.OptionSelected, "#graphql_field_list")
    def on_field_selected(self, event: OptionList.OptionSelected) -> None:
        option_index = getattr(event, "option_index", getattr(event, "index", -1))
        if option_index < 0 or option_index >= len(self._visible_root_fields):
            return
        self._select_root_field(self._visible_root_fields[option_index].name)

    @on(Input.Changed, "#graphql_field_search")
    def on_field_search_changed(self) -> None:
        self._refresh_field_list()

    @on(OptionList.OptionSelected, "#graphql_history_list")
    def on_history_selected(self, event: OptionList.OptionSelected) -> None:
        option_index = getattr(event, "option_index", getattr(event, "index", -1))
        if option_index < 0 or option_index >= len(self.state.history):
            return
        entry = self.state.history[option_index]
        self.query_one("#graphql_query_editor", TextArea).text = entry.query_text
        self.query_one("#graphql_variables_editor", TextArea).text = entry.variables_text
        self.query_one("#graphql_request_tabs", TabbedContent).active = "graphql_query_tab"
        self._set_response_summary(f"Loaded history item: {entry.title}")

    @on(Button.Pressed, "#graphql_send_button")
    def on_send_button_pressed(self) -> None:
        self.send_query_via_worker()

    @on(Button.Pressed, "#graphql_copy_response_button")
    def on_copy_response_button_pressed(self) -> None:
        body_text = self.query_one("#graphql_response_body", TextArea).text
        if not body_text.strip():
            self.notify("No response body to copy yet.", severity="warning")
            return
        self.copy_to_clipboard(body_text)
        self.notify("GraphQL response copied to clipboard.", severity="information")

    @on(Button.Pressed, "#graphql_build_field_button")
    def on_build_field_button_pressed(self) -> None:
        field = self._current_root_field()
        if field is None:
            self.notify("Select a root field first.", severity="warning")
            return
        self.query_one("#graphql_query_editor", TextArea).text = self._build_query_skeleton(field)
        self.query_one("#graphql_request_tabs", TabbedContent).active = "graphql_query_tab"
        self._set_response_summary(f"Built query skeleton for {field.name}.")

    @on(Button.Pressed, "#graphql_insert_args_button")
    def on_insert_args_button_pressed(self) -> None:
        field = self._current_root_field()
        if field is None:
            self.notify("Select a root field first.", severity="warning")
            return
        snippet = self._build_argument_snippet(field)
        if not snippet:
            self.notify("This field has no arguments.", severity="warning")
            return
        self._append_query_text(snippet)

    @on(Button.Pressed, "#graphql_insert_filters_button")
    def on_insert_filters_button_pressed(self) -> None:
        field = self._current_root_field()
        if field is None:
            self.notify("Select a root field first.", severity="warning")
            return
        snippet = self._build_named_argument_snippet(field, "filters")
        if not snippet:
            self.notify("This field does not expose a filters argument.", severity="warning")
            return
        self._append_query_text(snippet)

    @on(Button.Pressed, "#graphql_insert_pagination_button")
    def on_insert_pagination_button_pressed(self) -> None:
        field = self._current_root_field()
        if field is None:
            self.notify("Select a root field first.", severity="warning")
            return
        snippet = self._build_named_argument_snippet(field, "pagination")
        if not snippet:
            self.notify("This field does not expose a pagination argument.", severity="warning")
            return
        self._append_query_text(snippet)

    @on(Button.Pressed, "#graphql_insert_fragments_button")
    def on_insert_fragments_button_pressed(self) -> None:
        field = self._current_root_field()
        if field is None:
            self.notify("Select a root field first.", severity="warning")
            return
        snippet = self._build_fragment_snippet(field)
        if not snippet:
            self.notify("This field does not return a union/interface type.", severity="warning")
            return
        self._append_query_text(snippet)

    def watch_selected_field_name(self, selected_field_name: str | None) -> None:
        detail = self.query_one("#graphql_field_details", Static)
        context = self.query_one("#graphql_context_line", Static)
        if selected_field_name is None:
            detail.update("Select a root field to inspect its arguments and return type.")
            context.update("Field: <none>")
            return
        field = self._current_root_field()
        if field is None:
            return
        detail.update(self._field_detail_text(field))
        context.update(f"Field: {field.name}")

    def _theme_definition(self) -> ThemeDefinition:
        return self.theme_catalog.theme_for(self.theme_name)

    def _logo_renderable(self) -> Text:
        return logo_renderable(self.theme_catalog, self.theme_name)

    def _field_detail_text(self, field: GraphqlFieldInfo) -> Text:
        theme = self._theme_definition()
        lines = Text()
        lines.append(f"{field.name}\n", style=Style(color=theme.colors["primary"], bold=True))
        lines.append(f"Returns: {_type_label(field.type_ref)}\n")
        if field.description:
            lines.append(f"{field.description}\n")
        if field.args:
            lines.append("Arguments:\n", style=Style(color=theme.colors["secondary"], bold=True))
            for arg in field.args:
                default = f" = {arg.default_value}" if arg.default_value else ""
                lines.append(f"- {arg.name}: {_type_label(arg.type_ref)}{default}\n")
        else:
            lines.append("Arguments: none\n")
        return lines

    def _set_response_summary(self, content: Text | str) -> None:
        self.query_one("#graphql_response_summary", Static).update(content)

    def _current_root_field(self) -> GraphqlFieldInfo | None:
        if self._explorer is None or self.selected_field_name is None:
            return None
        for root_field in self._explorer.root_fields():
            if root_field.name == self.selected_field_name:
                return root_field
        return None

    def _refresh_field_list(self) -> None:
        option_list = self.query_one("#graphql_field_list", OptionList)
        if self._explorer is None:
            option_list.set_options(["Schema not loaded"])
            option_list.highlighted = None
            return
        search = self.query_one("#graphql_field_search", Input).value.strip().lower()
        self._visible_root_fields = [
            field
            for field in self._explorer.root_fields()
            if not search
            or search in field.name.lower()
            or search in _type_label(field.type_ref).lower()
            or search in (field.description or "").lower()
        ]
        if not self._visible_root_fields:
            option_list.set_options(["No matching root fields"])
            option_list.highlighted = None
            return
        theme = self._theme_definition()
        option_list.set_options(
            [
                Option(
                    Text.assemble(
                        (field.name, Style(color=theme.colors["primary"], bold=True)),
                        ("  "),
                        (
                            _type_label(field.type_ref),
                            Style(color=theme.variables["nb-muted-text"]),
                        ),
                    )
                )
                for field in self._visible_root_fields
            ]
        )
        if search:
            option_list.highlighted = 0
            self._select_root_field(self._visible_root_fields[0].name)
            return
        preferred_name = self.selected_field_name or self.state.selected_root_field
        if preferred_name:
            for index, field in enumerate(self._visible_root_fields):
                if field.name == preferred_name:
                    option_list.highlighted = index
                    self._select_root_field(field.name)
                    return
        option_list.highlighted = 0
        self._select_root_field(self._visible_root_fields[0].name)

    def _select_root_field(self, field_name: str) -> None:
        self.selected_field_name = field_name
        self.state.selected_root_field = field_name
        self.query_one("#graphql_sidebar_tabs", TabbedContent).active = "graphql_details_tab"

    def _render_history(self) -> None:
        history = self.query_one("#graphql_history_list", OptionList)
        if not self.state.history:
            history.set_options(["No saved queries yet"])
            history.highlighted = None
            return
        history.set_options([Option(entry.title) for entry in self.state.history])
        history.highlighted = 0

    def _append_query_text(self, snippet: str) -> None:
        editor = self.query_one("#graphql_query_editor", TextArea)
        current = editor.text.rstrip()
        editor.text = f"{current}\n\n{snippet}".strip()
        self.query_one("#graphql_request_tabs", TabbedContent).active = "graphql_query_tab"
        self._set_response_summary("Inserted GraphQL snippet into the query editor.")

    def _build_query_skeleton(self, field: GraphqlFieldInfo) -> str:
        args = self._build_argument_snippet(field)
        selection = self._build_selection_set(field.type_ref, depth=0)
        field_block = f"{field.name}{args}" if args else field.name
        if selection:
            field_block = f"{field_block} {selection}"
        return f"query {{\n  {field_block}\n}}"

    def _build_argument_snippet(self, field: GraphqlFieldInfo) -> str:
        if not field.args:
            return ""
        rendered = ", ".join(
            f"{arg.name}: {self._placeholder_for_type(arg.type_ref)}" for arg in field.args
        )
        return f"({rendered})"

    def _build_named_argument_snippet(self, field: GraphqlFieldInfo, name: str) -> str:
        target = next((arg for arg in field.args if arg.name == name), None)
        if target is None:
            return ""
        return f"{name}: {self._placeholder_for_type(target.type_ref)}"

    def _build_fragment_snippet(self, field: GraphqlFieldInfo) -> str:
        if self._explorer is None:
            return ""
        gql_type = self._explorer.named_type(field.type_ref)
        if (
            gql_type is None
            or gql_type.kind not in {"UNION", "INTERFACE"}
            or not gql_type.possible_types
        ):
            return ""
        parts: list[str] = []
        for possible_name in gql_type.possible_types[:3]:
            possible = self._explorer.types.get(possible_name)
            selection = self._selection_for_named_type(possible, depth=1)
            parts.append(f"... on {possible_name} {selection}")
        return "{\n  " + "\n  ".join(parts) + "\n}"

    def _selection_for_named_type(self, gql_type: GraphqlTypeInfo | None, depth: int) -> str:
        if gql_type is None:
            return "{ id }"
        indent = "  " * depth
        if gql_type.kind in {"OBJECT", "INTERFACE"} and gql_type.fields:
            picks = [field.name for field in gql_type.fields[:3]]
            if "id" in {field.name for field in gql_type.fields} and "id" not in picks:
                picks.insert(0, "id")
            return "{\n" + "\n".join(f"{indent}  {name}" for name in picks[:4]) + f"\n{indent}}}"
        if gql_type.kind == "UNION" and gql_type.possible_types:
            return (
                "{\n"
                + "\n".join(
                    f"{indent}  ... on {name} {{ id }}" for name in gql_type.possible_types[:2]
                )
                + f"\n{indent}}}"
            )
        return "{ id }"

    def _build_selection_set(self, type_ref: TypeRef, depth: int) -> str:
        if self._explorer is None:
            return ""
        gql_type = self._explorer.named_type(type_ref)
        if gql_type is None or gql_type.kind in {"SCALAR", "ENUM"}:
            return ""
        return self._selection_for_named_type(gql_type, depth + 1)

    def _placeholder_for_type(self, type_ref: TypeRef) -> str:
        if self._explorer is None:
            return "null"
        current = type_ref
        while current.kind == "NON_NULL" and current.of_type is not None:
            current = current.of_type
        if current.kind == "LIST" and current.of_type is not None:
            return f"[{self._placeholder_for_type(current.of_type)}]"
        named = self._explorer.named_type(current)
        name = self._explorer.named_type_name(current)
        if named is not None:
            if named.kind == "ENUM" and named.enum_values:
                return named.enum_values[0]
            if named.kind == "INPUT_OBJECT":
                lines = [
                    f"{field.name}: {self._placeholder_for_type(field.type_ref)}"
                    for field in named.input_fields[:3]
                ]
                if not lines:
                    return "{}"
                return "{ " + ", ".join(lines) + " }"
        if name in {"Int", "BigInt"}:
            return "0"
        if name == "Float":
            return "0.0"
        if name == "Boolean":
            return "true"
        if name in {"JSONString", "JSON"}:
            return '{ "key": "value" }'
        return '"value"'

    @work(group="graphql_schema", exclusive=True, thread=False)
    async def _load_schema(self) -> None:
        try:
            response = await self.client.graphql(_INTROSPECTION_QUERY)
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("GraphQL introspection returned a non-object payload.")
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                raise ValueError(self._graphql_error_summary(errors))
            data = payload.get("data")
            if not isinstance(data, dict):
                raise ValueError("GraphQL introspection did not include a data object.")
            self.post_message(GraphqlSchemaLoaded(_parse_explorer(data), None))
        except Exception as exc:  # noqa: BLE001
            detail = str(exc).strip() or exc.__class__.__name__
            self.post_message(GraphqlSchemaLoaded(None, detail))

    @on(GraphqlSchemaLoaded)
    def on_schema_loaded(self, event: GraphqlSchemaLoaded) -> None:
        self._explorer = event.explorer
        if event.error:
            self.query_one("#graphql_field_details", Static).update(
                f"Schema introspection unavailable.\n\n{event.error}\n\nManual query execution still works."
            )
            self._set_response_summary(
                "Schema introspection failed. The editor remains available for manual queries."
            )
            self.query_one("#graphql_field_list", OptionList).set_options(["Schema unavailable"])
            self.query_one("#graphql_field_list", OptionList).highlighted = None
            return
        self._refresh_field_list()
        self._set_response_summary("Schema loaded. Select a root field or build a query skeleton.")

    def _parse_variables_text(self) -> dict[str, Any] | None:
        raw = self.query_one("#graphql_variables_editor", TextArea).text.strip()
        if not raw:
            return None
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("GraphQL variables must decode to a JSON object.")
        return parsed

    @work(group="graphql_query", exclusive=True, thread=False)
    async def send_query_via_worker(self) -> None:
        try:
            query_text = self.query_one("#graphql_query_editor", TextArea).text.strip()
            if not query_text:
                raise ValueError("GraphQL query cannot be empty.")
            variables = self._parse_variables_text()
        except Exception as exc:  # noqa: BLE001
            self._set_request_error(str(exc).strip() or exc.__class__.__name__)
            return

        self._set_request_in_flight()
        started = perf_counter()
        try:
            response = await self.client.graphql(query_text, variables)
        except Exception as exc:  # noqa: BLE001
            self._set_request_error(str(exc).strip() or exc.__class__.__name__)
            return

        self.post_message(
            GraphqlResponseReceived(
                response,
                GraphqlExecution(
                    query_text=query_text,
                    variables=variables,
                    duration_ms=(perf_counter() - started) * 1000,
                ),
            )
        )

    @on(GraphqlResponseReceived)
    def on_response_received(self, event: GraphqlResponseReceived) -> None:
        self._render_response(event.response, event.execution)

    def _set_request_in_flight(self) -> None:
        theme = self._theme_definition()
        self.query_one("#graphql_response_status", Static).update(
            Text("Running GraphQL query", style=Style(color=theme.colors["primary"], bold=True))
        )
        self.query_one("#graphql_response_timing", Static).update("...")
        self.query_one("#graphql_response_size", Static).update("...")
        self.query_one("#graphql_copy_response_button", Button).disabled = True
        self._set_response_summary("Query in flight against the current NetBoxApiClient.")

    def _set_request_error(self, message: str) -> None:
        self.query_one("#graphql_response_status", Static).update(
            Text("GraphQL request failed", style=f"bold {self._theme_definition().colors['error']}")
        )
        self.query_one("#graphql_response_timing", Static).update("-")
        self.query_one("#graphql_response_size", Static).update("-")
        self.query_one("#graphql_response_body", TextArea).text = message
        self.query_one("#graphql_response_headers", TextArea).text = ""
        self.query_one("#graphql_copy_response_button", Button).disabled = not bool(message.strip())
        self._set_response_summary(message)
        self.notify(message, severity="error")

    def _graphql_error_summary(self, errors: list[Any]) -> str:
        messages = [
            str(item.get("message") or "GraphQL error") for item in errors if isinstance(item, dict)
        ]
        if not messages:
            return "GraphQL errors were returned."
        return "; ".join(messages[:3])

    def _render_response(self, response: ApiResponse, execution: GraphqlExecution) -> None:
        payload: dict[str, Any] | None = None
        errors_summary: str | None = None
        try:
            parsed = response.json()
            if isinstance(parsed, dict):
                payload = parsed
                errors = parsed.get("errors")
                if isinstance(errors, list) and errors:
                    errors_summary = self._graphql_error_summary(errors)
        except Exception:  # noqa: BLE001
            payload = None

        theme = self._theme_definition()
        status_text = f"HTTP {response.status}"
        style = Style(color=theme.colors["primary"], bold=True)
        if errors_summary:
            status_text = f"HTTP {response.status} / GraphQL errors"
            style = Style(color=theme.colors["error"], bold=True)
        self.query_one("#graphql_response_status", Static).update(Text(status_text, style=style))
        self.query_one("#graphql_response_timing", Static).update(f"{execution.duration_ms:.1f} ms")
        self.query_one("#graphql_response_size", Static).update(
            f"{len(response.text.encode('utf-8'))} B"
        )
        body_text = self._format_response_body(response.text)
        self.query_one("#graphql_response_body", TextArea).text = body_text
        self.query_one("#graphql_response_headers", TextArea).text = self._format_headers(
            response.headers
        )
        self.query_one("#graphql_copy_response_button", Button).disabled = not bool(
            body_text.strip()
        )
        summary_lines = [
            f"Query length: {len(execution.query_text)} chars",
            f"Variables: {'yes' if execution.variables else 'no'}",
        ]
        if payload and isinstance(payload.get("data"), dict):
            summary_lines.append("Data keys: " + ", ".join(sorted(payload["data"].keys())[:8]))
        if errors_summary:
            summary_lines.append(f"Errors: {errors_summary}")
            self.notify(errors_summary, severity="error")
        self._set_response_summary("\n".join(summary_lines))
        self.query_one("#graphql_response_tabs", TabbedContent).active = "graphql_response_body_tab"
        self._record_history(
            query_text=execution.query_text,
            variables_text=self.query_one("#graphql_variables_editor", TextArea).text.strip(),
        )

    def _record_history(self, *, query_text: str, variables_text: str) -> None:
        title = next((line.strip() for line in query_text.splitlines() if line.strip()), "Query")
        title = title[:80]
        fresh = GraphqlHistoryEntry(
            title=title, query_text=query_text, variables_text=variables_text
        )
        history = [
            item
            for item in self.state.history
            if not (item.query_text == query_text and item.variables_text == variables_text)
        ]
        history.insert(0, fresh)
        self.state.history = history[:15]
        self._render_history()

    def _format_response_body(self, body_text: str) -> str:
        try:
            return json.dumps(json.loads(body_text), indent=2, sort_keys=True)
        except json.JSONDecodeError:
            return body_text

    def _format_headers(self, headers: dict[str, str]) -> str:
        if not headers:
            return ""
        return "\n".join(f"{key}: {value}" for key, value in sorted(headers.items()))

    @work(group="graphql_connection_probe", exclusive=True, thread=False)
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

    def _set_connection_badge_checking(self) -> None:
        set_connection_badge_state(self, badge_id="#graphql_connection_badge", state="checking")

    def _render_connection_status(self, probe: ConnectionProbe) -> None:
        set_connection_badge_state(
            self,
            badge_id="#graphql_connection_badge",
            state=badge_state_for_probe(probe),
        )

    def _update_clock(self) -> None:
        update_clock_widget(self, widget_id="#graphql_clock")

    def _apply_theme(self, theme_name: str, notify: bool = False) -> None:
        self.theme_name = apply_theme(
            self,
            theme_catalog=self.theme_catalog,
            theme_options=self.theme_options,
            current_theme_name=self.theme_name,
            new_theme_name=theme_name,
            state=self.state,
            logo_widget_id="#graphql_logo",
            notify=notify,
        )
        self._sync_text_area_syntax_themes()
        self._sync_theme_surfaces()
        if self._explorer is not None:
            self._refresh_field_list()

    def _sync_text_area_syntax_themes(self) -> None:
        ta_theme = _text_area_syntax_theme_for(self.theme_name)
        for widget in self.query(TextArea):
            widget.theme = ta_theme

    def _sync_theme_surfaces(self) -> None:
        theme = self._theme_definition()
        background = theme.colors["background"]
        surface = theme.colors["surface"]
        panel = theme.colors["panel"]
        primary = theme.colors["primary"]
        border = theme.variables["nb-border-subtle"]
        muted = theme.variables["nb-muted-text"]

        def _set(selector: str, css: str) -> None:
            try:
                self.query_one(selector).set_styles(css)
            except NoMatches:
                return

        for selector in ("#graphql_builder_panel", "#graphql_response_panel", "#graphql_sidebar"):
            _set(selector, f"background: {surface}; background-tint: transparent;")
        for selector in (
            "#graphql_field_list",
            "#graphql_history_list",
            "#graphql_query_editor",
            "#graphql_variables_editor",
            "#graphql_response_body",
            "#graphql_response_headers",
        ):
            _set(selector, f"background: {background}; background-tint: transparent;")
        for selector in (
            "#graphql_request_tabs",
            "#graphql_response_tabs",
            "#graphql_sidebar_tabs",
            "#graphql_request_tabs ContentSwitcher",
            "#graphql_response_tabs ContentSwitcher",
            "#graphql_sidebar_tabs ContentSwitcher",
            "#graphql_details_tab",
            "#graphql_history_tab",
            "#graphql_query_tab",
            "#graphql_variables_tab",
            "#graphql_response_body_tab",
            "#graphql_response_headers_tab",
            "#graphql_response_summary_tab",
        ):
            _set(selector, f"background: {surface}; background-tint: transparent;")
        _set("#graphql_response_meta", f"background: {panel}; background-tint: transparent;")
        _set(
            "#graphql_send_button",
            f"background: {primary} 12%; color: {primary}; border: round {primary}; "
            "tint: transparent; background-tint: transparent;",
        )
        _set(
            "#graphql_build_field_button",
            f"background: {primary} 12%; color: {primary}; border: round {primary}; "
            "tint: transparent; background-tint: transparent;",
        )
        for selector in (
            "#graphql_insert_args_button",
            "#graphql_insert_filters_button",
            "#graphql_insert_pagination_button",
            "#graphql_insert_fragments_button",
            "#graphql_copy_response_button",
        ):
            _set(
                selector,
                f"background: transparent; color: {muted}; border: round {border}; "
                "tint: transparent; background-tint: transparent;",
            )

    def _strip_theme_select_prefix(self) -> None:
        strip_theme_select_prefix(
            self,
            selector="#graphql_theme_select SelectCurrent Static#label",
        )
        strip_theme_select_prefix(
            self,
            selector="#graphql_view_select SelectCurrent Static#label",
        )


def available_theme_names() -> tuple[str, ...]:
    return get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return get_theme_catalog().resolve(theme_name)


def run_graphql_tui(
    client: NetBoxApiClient,
    theme_name: str | None = None,
) -> None:
    try:
        NetBoxGraphqlTuiApp(client=client, theme_name=theme_name).run()
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        raise RuntimeError(f"Unable to launch the GraphQL TUI: {detail}") from None
