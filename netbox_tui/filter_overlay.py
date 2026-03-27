"""Filter overlay mixin for NetBoxTuiApp.

Extracts all filter-field selection, filter-overlay dialog, and active-filter
display logic into a reusable mixin.  ``NetBoxTuiApp`` inherits this mixin so
the main ``app.py`` stays focused on layout composition and data loading.

Attributes expected on the host class (set in ``NetBoxTuiApp.__init__``):
    index: SchemaIndex
    current_group: str | None
    current_resource: str | None
    _filter_fields: list[tuple[str, str]]
    _visible_filter_fields: list[tuple[str, str]]
    _selected_filter_key: str
    _filter_overlay_field: str
"""

from __future__ import annotations

from textual import on
from textual.containers import Vertical
from textual.css.query import NoMatches
from textual.widgets import Button, Input, OptionList, Static

from netbox_sdk.formatting import humanize_field
from netbox_tui.widgets import NbxButton

_TEXT_CONTAINS_FILTER_FIELDS: frozenset[str] = frozenset(
    {
        "asset_tag",
        "comments",
        "description",
        "display",
        "mac_address",
        "model",
        "name",
        "part_number",
        "serial",
        "serial_number",
        "slug",
        "username",
        "vendor_name",
    }
)


class FilterOverlayMixin:
    """Mixin that adds filter-overlay and filter-picker behaviour to a Textual App."""

    # ── public action ─────────────────────────────────────────────────────────

    def action_filter_modal(self) -> None:
        default_key = self._selected_filter_field()
        if not default_key and self._filter_fields:
            default_key = self._filter_fields[0][1]
        if not default_key:
            self.notify("No filterable fields loaded yet", severity="warning")
            return
        self._open_filter_picker(default_key)

    def action_cancel(self) -> None:
        picker_overlay = self.query_one("#filter_picker_overlay", Vertical)
        if "hidden" not in picker_overlay.classes:
            self._close_filter_picker()
            return
        overlay = self.query_one("#filter_overlay", Vertical)
        if "hidden" not in overlay.classes:
            self._close_filter_overlay()

    # ── event handlers ────────────────────────────────────────────────────────

    @on(Input.Submitted, "#filter_value")
    def on_filter_value_submit(self) -> None:
        self._apply_filter_overlay()

    @on(Input.Changed, "#filter_picker_search")
    def on_filter_picker_search_changed(self) -> None:
        self._refresh_filter_picker_list()

    @on(Input.Submitted, "#filter_picker_search")
    def on_filter_picker_search_submitted(self) -> None:
        if self._visible_filter_fields:
            self._open_filter_overlay(self._visible_filter_fields[0][1])

    @on(OptionList.OptionSelected, "#filter_picker_list")
    def on_filter_picker_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id != "filter_picker_list":
            return
        option_index = getattr(event, "option_index", getattr(event, "index", -1))
        if option_index < 0 or option_index >= len(self._visible_filter_fields):
            return
        self._open_filter_overlay(self._visible_filter_fields[option_index][1])

    @on(NbxButton.Pressed, "#filter_select")
    def on_filter_select_pressed(self) -> None:
        self.action_filter_modal()

    @on(NbxButton.Pressed, "#filter_apply")
    def on_filter_apply_pressed(self) -> None:
        self._apply_filter_overlay()

    @on(NbxButton.Pressed, "#filter_cancel")
    def on_filter_cancel_pressed(self) -> None:
        self._close_filter_overlay()

    @on(NbxButton.Pressed, "#filter_picker_cancel")
    def on_filter_picker_cancel_pressed(self) -> None:
        self._close_filter_picker()

    # ── filter-fields management ──────────────────────────────────────────────

    def _refresh_filter_fields(self, group: str, resource: str) -> None:
        """Populate the filter field dropdown from the OpenAPI schema (no HTTP required)."""
        from netbox_sdk.schema import FilterParam  # noqa: PLC0415

        params: list[FilterParam] = self.index.filter_params(group, resource)
        current = self._selected_filter_field()

        structured_params = [param for param in params if param.name != "q"]
        name_to_label = {param.name: param.label for param in structured_params}
        ordered_names = self._order_field_names_for_filter(list(name_to_label))
        ordered: list[tuple[str, str]] = [(name_to_label[name], name) for name in ordered_names]
        self._filter_fields = ordered
        self._visible_filter_fields = list(ordered)
        if current and any(value == current for _, value in ordered):
            self._selected_filter_key = current
        else:
            self._selected_filter_key = ""
        self._update_filter_select_label()
        self._update_active_filters()

    def _order_field_names_for_filter(self, names: list[str]) -> list[str]:
        from netbox_sdk.formatting import order_field_names  # noqa: PLC0415

        return order_field_names(names)

    def _selected_filter_field(self) -> str:
        if not any(
            field_value == self._selected_filter_key for _, field_value in self._filter_fields
        ):
            return ""
        return self._selected_filter_key

    def _update_filter_select_label(self) -> None:
        label = "Filter Field"
        if self._selected_filter_key:
            label = humanize_field(self._selected_filter_key)
        self.query_one("#filter_select", Button).label = label

    # ── filter picker dialog ──────────────────────────────────────────────────

    def _open_filter_picker(self, preferred_field: str = "") -> None:
        if not self._filter_fields:
            self.notify("No filterable fields loaded yet", severity="warning")
            return
        self._close_filter_overlay()
        overlay = self.query_one("#filter_picker_overlay", Vertical)
        search = self.query_one("#filter_picker_search", Input)
        search.value = ""
        overlay.remove_class("hidden")
        self._refresh_filter_picker_list(preferred_field=preferred_field)
        search.focus()

    def _close_filter_picker(self) -> None:
        self.query_one("#filter_picker_overlay", Vertical).add_class("hidden")
        self.query_one("#filter_picker_search", Input).value = ""
        self._visible_filter_fields = list(self._filter_fields)

    def _refresh_filter_picker_list(self, preferred_field: str = "") -> None:
        search = self.query_one("#filter_picker_search", Input)
        option_list = self.query_one("#filter_picker_list", OptionList)
        needle = search.value.strip().lower()
        self._visible_filter_fields = [
            field
            for field in self._filter_fields
            if not needle or needle in field[0].lower() or needle in field[1].lower()
        ]
        prompts = [label for label, _ in self._visible_filter_fields]
        if not prompts:
            prompts = ["No matching fields"]
        option_list.set_options(prompts)
        if self._visible_filter_fields:
            highlight_index = 0
            if preferred_field:
                for index, (_, value) in enumerate(self._visible_filter_fields):
                    if value == preferred_field:
                        highlight_index = index
                        break
            option_list.highlighted = highlight_index
        else:
            option_list.highlighted = None

    # ── filter overlay dialog ─────────────────────────────────────────────────

    def _open_filter_overlay(self, field_name: str) -> None:
        self._filter_overlay_field = field_name
        self._selected_filter_key = field_name
        self._close_filter_picker()
        overlay = self.query_one("#filter_overlay", Vertical)
        label = self.query_one("#filter_field_label", Static)
        value_input = self.query_one("#filter_value", Input)
        self._update_filter_select_label()
        label.update(f"Field: {humanize_field(field_name)}")
        value_input.value = self._current_filter_value(field_name)
        overlay.remove_class("hidden")
        value_input.focus()

    def _close_filter_overlay(self) -> None:
        self._filter_overlay_field = ""
        try:
            self.query_one("#filter_overlay", Vertical).add_class("hidden")
            self.query_one("#filter_value", Input).value = ""
        except NoMatches:
            pass

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
        return self._parse_filter_pairs(self.query_one("#global_search", Input).value.strip()).get(
            key, ""
        )

    def _set_filter_query(self, key: str, value: str) -> None:
        search = self.query_one("#global_search", Input)
        pairs = self._parse_filter_pairs(search.value.strip())
        if value:
            pairs[key] = value
        else:
            pairs.pop(key, None)
        search.value = ", ".join(f"{name}={pairs[name]}" for name in sorted(pairs))
        self._update_active_filters()

    # ── search parsing helpers ────────────────────────────────────────────────

    def _query_from_search(self, raw: str) -> dict[str, str]:
        raw = raw.strip()
        if not raw:
            return {}

        if "=" not in raw:
            return {"q": raw}

        parsed = self._parse_filter_pairs(raw)
        if not parsed:
            return {"q": raw}
        return self._normalize_filter_pairs(parsed)

    def _normalize_filter_pairs(self, pairs: dict[str, str]) -> dict[str, str]:
        group = getattr(self, "current_group", None)
        resource = getattr(self, "current_resource", None)
        index = getattr(self, "index", None)
        if not group or not resource or index is None:
            return dict(pairs)

        normalized: dict[str, str] = {}
        for key, value in pairs.items():
            lookup_key = self._preferred_filter_lookup(group, resource, key)
            normalized[lookup_key] = value
        return normalized

    def _preferred_filter_lookup(self, group: str, resource: str, key: str) -> str:
        if "__" in key or key not in _TEXT_CONTAINS_FILTER_FIELDS:
            return key

        query_param_names = self._query_param_names(group, resource)
        contains_lookup = f"{key}__ic"
        if contains_lookup in query_param_names:
            return contains_lookup
        return key

    def _query_param_names(self, group: str, resource: str) -> set[str]:
        index = getattr(self, "index", None)
        if index is None:
            return set()
        paths = getattr(index, "schema", {}).get("paths", {})
        if not isinstance(paths, dict):
            return set()
        path_item = paths.get(f"/api/{group}/{resource}/", {})
        if not isinstance(path_item, dict):
            return set()
        get_op = path_item.get("get", {})
        if not isinstance(get_op, dict):
            return set()
        parameters = get_op.get("parameters", [])
        if not isinstance(parameters, list):
            return set()
        return {
            str(param.get("name", ""))
            for param in parameters
            if isinstance(param, dict) and param.get("in") == "query" and str(param.get("name", ""))
        }

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
        chips = ", ".join(f"{humanize_field(key)}={value}" for key, value in sorted(pairs.items()))
        target.update(f"Filters: {chips}")
