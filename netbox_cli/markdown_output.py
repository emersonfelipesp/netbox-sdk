"""Markdown rendering helpers for API JSON payloads."""

from __future__ import annotations

import json
from typing import Any

from .output_safety import sanitize_terminal_text
from .ui.formatting import humanize_field, order_field_names

_LIST_COLUMNS = {
    "id",
    "name",
    "display",
    "status",
    "type",
    "role",
    "site",
    "location",
    "device",
    "interface",
    "ip",
    "address",
    "prefix",
    "vlan",
    "tenant",
}


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _cell_text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return sanitize_terminal_text(value)
    if isinstance(value, (dict, list)):
        return sanitize_terminal_text(_compact_json(value))
    return sanitize_terminal_text(str(value))


def _rows_to_markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""

    header = rows[0]
    body = rows[1:]
    header_line = "| " + " | ".join(_escape_markdown_cell(cell) for cell in header) + " |"
    separator = "| " + " | ".join("---" for _ in header) + " |"
    body_lines = [
        "| " + " | ".join(_escape_markdown_cell(cell) for cell in row) + " |" for row in body
    ]
    return "\n".join([header_line, separator, *body_lines])


def _ordered_keys_for_rows(rows: list[dict[str, Any]]) -> list[str]:
    all_keys: list[str] = []
    for row in rows:
        for key in row.keys():
            key_s = str(key)
            if key_s not in all_keys:
                all_keys.append(key_s)

    priority_keys = [k for k in all_keys if k in _LIST_COLUMNS]
    return order_field_names(priority_keys if priority_keys else all_keys)


def _render_dict_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "No results."
    keys = _ordered_keys_for_rows(rows)
    header = [humanize_field(key) for key in keys]
    body = [[_cell_text(row.get(key)) for key in keys] for row in rows]
    return _rows_to_markdown_table([header, *body])


def render_markdown(payload: Any) -> str:
    """Render API payloads to table-first markdown text."""
    if isinstance(payload, dict) and "results" in payload and isinstance(payload["results"], list):
        rows = [item for item in payload["results"] if isinstance(item, dict)]
        if rows:
            return _render_dict_rows(rows)
        if payload["results"]:
            scalar_rows = [{"value": _cell_text(item)} for item in payload["results"]]
            return _render_dict_rows(scalar_rows)
        return "No results."

    if isinstance(payload, list):
        dict_rows = [item for item in payload if isinstance(item, dict)]
        if dict_rows:
            return _render_dict_rows(dict_rows)
        if payload:
            scalar_rows = [{"value": _cell_text(item)} for item in payload]
            return _render_dict_rows(scalar_rows)
        return "No results."

    if isinstance(payload, dict):
        keys = order_field_names([str(key) for key in payload.keys()])
        rows: list[list[str]] = [["Field", "Value"]]
        rows.extend([[humanize_field(key), _cell_text(payload.get(key))] for key in keys])
        return _rows_to_markdown_table(rows)

    return _escape_markdown_cell(_cell_text(payload))
