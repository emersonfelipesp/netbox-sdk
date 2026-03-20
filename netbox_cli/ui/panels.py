from __future__ import annotations

from typing import Any

from textual.containers import Vertical
from textual.timer import Timer
from textual.widgets import DataTable, Static

from .formatting import humanize_field, order_field_names, semantic_cell


class PanelCard(Vertical):
    """Simple card-like container with title and optional subtitle."""

    def __init__(self, title: str, subtitle: str = "", *, panel_id: str | None = None):
        super().__init__(id=panel_id)
        self._title_text = title
        self._subtitle_text = subtitle

    def compose(self):
        yield Static(self._title_text, classes="panel-title")
        if self._subtitle_text:
            yield Static(self._subtitle_text, classes="panel-subtitle")


class ObjectAttributesPanel(PanelCard):
    """Render selected row data as key/value attributes."""

    def __init__(self, *, panel_id: str = "detail_panel"):
        super().__init__(
            "Object Attributes", "NetBox detail-style panel", panel_id=panel_id
        )
        self._spinner_frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self._spinner_index = 0
        self._spinner_timer: Timer | None = None
        self._row_values: list[tuple[str, Any]] = []

    def compose(self):
        yield from super().compose()
        yield Static("Ready", id="detail_status")
        table = DataTable(id="detail_table")
        table.cursor_type = "cell"
        table.add_columns("Field", "Value")
        table.add_row("status", "Select a row in Results tab")
        yield table

    def _set_status(self, text: str) -> None:
        self.query_one("#detail_status", Static).update(text)

    def _stop_spinner(self) -> None:
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None

    def _spinner_tick(self, label: str) -> None:
        frame = self._spinner_frames[self._spinner_index % len(self._spinner_frames)]
        self._spinner_index += 1
        self._set_status(f"{frame} {label}")

    def set_loading(self, label: str = "Loading object details...") -> None:
        self._stop_spinner()
        self._spinner_index = 0
        self._row_values = []
        self._spinner_tick(label)
        self._spinner_timer = self.set_interval(0.12, lambda: self._spinner_tick(label))
        self.add_class("-loading")  # CSS state machine: drives teal status color

        table = self.query_one("#detail_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Field", "Value")
        table.add_row("status", "Loading...")

    def set_object(self, obj: dict[str, Any] | None) -> None:
        self._stop_spinner()
        self.remove_class("-loading")  # Clear CSS loading state
        self._row_values = []
        table = self.query_one("#detail_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Field", "Value")

        if not obj:
            self._set_status("No object selected")
            table.add_row("status", "No object selected")
            return

        self._set_status("Loaded")
        ordered = order_field_names([str(key) for key in obj.keys()])
        for key in ordered:
            raw_value = obj.get(key)
            field = humanize_field(str(key))
            self._row_values.append((field, raw_value))
            table.add_row(field, semantic_cell(str(key), raw_value, max_len=500))

    def detail_value_at(self, row_index: int) -> Any | None:
        if row_index < 0 or row_index >= len(self._row_values):
            return None
        return self._row_values[row_index][1]
