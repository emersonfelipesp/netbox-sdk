from __future__ import annotations

from netbox_cli.output_safety import sanitize_terminal_text
from netbox_cli.ui.formatting import humanize_value, semantic_cell


def test_sanitize_terminal_text_strips_ansi_sequences() -> None:
    rendered = sanitize_terminal_text("hello\x1b[31mred\x1b[0mworld")

    assert rendered == "helloredworld"


def test_sanitize_terminal_text_replaces_control_characters() -> None:
    rendered = sanitize_terminal_text("name\x00value\x07")

    assert rendered == "name\ufffdvalue\ufffd"


def test_humanize_value_sanitizes_untrusted_strings() -> None:
    rendered = humanize_value("leaf\x1b]8;;https://evil.example\x1b\\link\x1b]8;;\x1b\\")

    assert "\x1b" not in rendered
    assert "leaflink" in rendered


def test_semantic_cell_sanitizes_rich_text_content() -> None:
    cell = semantic_cell("name", "[bold]unsafe[/bold]\x1b[31m")

    assert cell.plain == "[bold]unsafe[/bold]"
