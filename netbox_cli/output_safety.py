from __future__ import annotations

import re
from typing import Any

from rich.text import Text

_ANSI_ESCAPE_RE = re.compile(
    r"\x1b(?:\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
)


def sanitize_terminal_text(value: Any) -> str:
    text = str(value)
    text = _ANSI_ESCAPE_RE.sub("", text)
    return "".join(_sanitize_char(char) for char in text)


def safe_text(value: Any, *, style: str | None = None) -> Text:
    return Text(sanitize_terminal_text(value), style=style or "")


def _sanitize_char(char: str) -> str:
    if char in {"\n", "\r", "\t"}:
        return char
    if ord(char) < 0x20 or ord(char) == 0x7F:
        return "\uFFFD"
    return char
