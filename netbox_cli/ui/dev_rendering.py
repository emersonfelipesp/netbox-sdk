"""Pure rendering helpers for the NetBox Dev TUI.

All functions here are stateless: they accept a ``ThemeDefinition`` and data
values, and return ``Rich`` ``Text`` objects or style strings.  Keeping them
at module level (rather than as instance methods on ``NetBoxDevTuiApp``) makes
them independently testable and keeps ``dev_app.py`` focused on Textual widget
composition and event handling.
"""

from __future__ import annotations

import json

from rich.style import Style
from rich.text import Text

from netbox_cli.api import ApiResponse
from netbox_cli.schema import Operation
from netbox_cli.theme_registry import ThemeDefinition

from .dev_state import RequestExecution


def http_method_style(theme: ThemeDefinition, method: str) -> str:
    """Return a Rich style string for the given HTTP method."""
    colors = theme.colors
    match method.strip().upper():
        case "GET":
            return f"bold {colors['success']}"
        case "POST":
            return f"bold {colors['primary']}"
        case "PUT":
            return f"bold {colors['warning']}"
        case "PATCH":
            return f"bold {colors['accent']}"
        case "DELETE":
            return f"bold {colors['error']}"
        case _:
            return f"bold {colors['secondary']}"


def path_muted_style(theme: ThemeDefinition) -> Style:
    """Return a muted Rich ``Style`` for path text."""
    return Style(color=theme.variables["nb-muted-text"], dim=True)


def operation_line_text(theme: ThemeDefinition, method: str, path: str) -> Text:
    """One-line ``Text`` rendering of an HTTP method + path."""
    line = Text()
    line.append(method.upper(), style=http_method_style(theme, method))
    line.append(" ")
    line.append(path, style=path_muted_style(theme))
    return line


def operation_detail_text(theme: ThemeDefinition, operation: Operation, summary: str) -> Text:
    """Multi-line ``Text`` rendering of an operation with its summary."""
    block = Text()
    block.append(operation.method.upper(), style=http_method_style(theme, operation.method))
    block.append(" ")
    block.append(operation.path, style=path_muted_style(theme))
    block.append("\n")
    block.append(summary, style=Style(color=theme.variables["nb-muted-text"]))
    return block


def http_status_code_style(theme: ThemeDefinition, status: int) -> str:
    """Return a Rich style string for an HTTP status code."""
    colors = theme.colors
    if 200 <= status < 300:
        return f"bold {colors['success']}"
    if 300 <= status < 400:
        return f"bold {colors['primary']}"
    if 400 <= status < 500:
        return f"bold {colors['warning']}"
    if status >= 500:
        return f"bold {colors['error']}"
    return f"bold {colors['secondary']}"


def response_status_line(theme: ThemeDefinition, status: int) -> Text:
    """``Text`` rendering of ``HTTP <status>`` with semantic color."""
    line = Text()
    line.append("HTTP ", style="dim")
    line.append(str(status), style=http_status_code_style(theme, status))
    return line


def sending_status_line(theme: ThemeDefinition, method: str, path: str) -> Text:
    """``Text`` rendering of ``Sending <METHOD> <path>``."""
    line = Text()
    line.append("Sending ", style="dim")
    line.append(method.upper(), style=http_method_style(theme, method))
    line.append(" ")
    line.append(path, style=path_muted_style(theme))
    return line


def prepared_request_text(theme: ThemeDefinition, method: str, path: str) -> Text:
    """``Text`` rendering of ``Prepared <METHOD> <path>``."""
    line = Text()
    line.append("Prepared ", style="dim")
    line.append(method.upper(), style=http_method_style(theme, method))
    line.append(" ")
    line.append(path, style=path_muted_style(theme))
    return line


def completed_response_summary(
    theme: ThemeDefinition, execution: RequestExecution, response: ApiResponse
) -> Text:
    """Multi-line summary ``Text`` shown in the response panel after a completed request."""
    muted = Style(color=theme.variables["nb-muted-text"])
    query_text = "&".join(f"{key}={value}" for key, value in execution.query.items()) or "-"
    payload_text = (
        "none"
        if execution.payload is None
        else json.dumps(execution.payload, indent=2, sort_keys=True)
    )
    block = Text()
    block.append(execution.method.upper(), style=http_method_style(theme, execution.method))
    block.append(" ")
    block.append(execution.path, style=path_muted_style(theme))
    block.append("\n")
    block.append("Query: ", style="dim")
    block.append(query_text, style=muted)
    block.append("\n")
    block.append("Payload: ", style="dim")
    block.append(payload_text, style=muted)
    block.append("\n")
    block.append("Status: ", style="dim")
    block.append(str(response.status), style=http_status_code_style(theme, response.status))
    return block
