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
    cp = ord(char)
    # C0 controls (< 0x20), DEL (0x7F), and C1 controls (0x80–0x9F).
    # C1 includes CSI (U+009B) and OSC (U+009D) which some terminals treat
    # as escape-sequence initiators without a leading ESC byte.
    if cp < 0x20 or cp == 0x7F or 0x80 <= cp <= 0x9F:
        return "\uFFFD"
    return char
