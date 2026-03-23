"""Output format conversion — JSON to YAML / Markdown.

Single Responsibility: pure data transformation, no I/O or CLI logic.
Open/Closed: new formats can be added by extending ``FormatVariant``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import yaml

from ..markdown_output import render_markdown
from .models import strip_status_header


@dataclass(frozen=True, slots=True)
class FormatVariant:
    """The three structured output formats derived from a single JSON response."""

    json_text: str
    yaml_text: str
    markdown_text: str


def _parse_cli_json_output(raw: str) -> Any | None:
    """Extract and parse JSON from CLI ``--json`` output.

    ``print_response`` prepends ``Status: NNN\\n`` before the JSON body.
    Returns ``None`` when the output is not valid JSON (help text, errors).
    """
    body = strip_status_header(raw).strip()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def convert_json_to_variants(json_cli_output: str) -> FormatVariant | None:
    """Convert raw ``--json`` CLI output to JSON + YAML + Markdown.

    Returns ``None`` when the input is not valid JSON (help banners,
    local commands, error output).

    This is the single point of format conversion — callers never need
    to import ``yaml`` or ``markdown_output`` directly.
    """
    parsed = _parse_cli_json_output(json_cli_output)
    if parsed is None:
        return None

    return FormatVariant(
        json_text=json.dumps(parsed, indent=2, sort_keys=True),
        yaml_text=yaml.dump(
            parsed,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ).rstrip(),
        markdown_text=render_markdown(parsed),
    )
