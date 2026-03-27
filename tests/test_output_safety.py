"""Tests for terminal text sanitization and safe Rich formatting helpers."""

from __future__ import annotations

import pytest

from netbox_sdk.formatting import humanize_value, semantic_cell
from netbox_sdk.output_safety import sanitize_terminal_text

pytestmark = pytest.mark.suite_sdk


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


def test_sanitize_terminal_text_strips_c1_control_characters() -> None:
    # U+009B = CSI, U+009D = OSC — C1 codes some terminals interpret as
    # escape-sequence initiators without a leading ESC byte.
    rendered = sanitize_terminal_text("hello\x9bworld\x9d")

    assert rendered == "hello\ufffdworld\ufffd"


def test_sanitize_terminal_text_neutralises_c1_csi_sequence() -> None:
    # "\x9b31m" is the C1 equivalent of "\x1b[31m" (red colour).
    # After sanitisation the CSI byte is replaced but printable bytes remain;
    # the sequence is broken and no terminal will colour the output.
    rendered = sanitize_terminal_text("\x9b31mred\x9b0m")

    assert "\x9b" not in rendered
    assert "red" in rendered
    # CSI byte must be replaced, not silently dropped.
    assert rendered.startswith("\ufffd")
