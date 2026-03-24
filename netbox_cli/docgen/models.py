"""Value objects and constants for the docgen capture pipeline.

Single Responsibility: defines data shapes and shared constants only.
No I/O, no CLI logic, no format conversion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# ── Concurrency defaults ─────────────────────────────────────────────────────
# Max parallel CLI captures.  NetBox demo handles ~4 concurrent fine;
# production instances may want lower values.
DEFAULT_MAX_CONCURRENCY: int = 4

# ── Output format support ────────────────────────────────────────────────────
_OUTPUT_FORMAT_FLAGS: frozenset[str] = frozenset({"--json", "--yaml", "--markdown"})

# Local commands whose output is plain text (no API response to format).
_LOCAL_COMMANDS: frozenset[str] = frozenset(
    {"groups", "resources", "ops", "config", "logs", "init"}
)

# ── Error detection ──────────────────────────────────────────────────────────
# Strings that indicate a command failed because configuration is missing.
# These commands are skipped entirely — they are not useful documentation.
CONFIG_ERROR_SIGNALS: tuple[str, ...] = (
    "NetBox endpoint configuration is required",
    "NetBox host (example:",
    "Aborted.",
)

# Regex for the "Status: NNN" header prepended by ``print_response``.
# Stripped from format-variant captures so JSON/YAML/MD are clean.
_STATUS_HEADER_RE = re.compile(r"^Status:\s*\d+\s*\n?")


# ── Value objects ────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class CaptureSpec:
    """A single command to capture for documentation.

    Mirrors ``docgen_specs.CaptureSpec`` but uses stdlib dataclass
    instead of Pydantic so the docgen package has zero framework deps.
    """

    section: str
    title: str
    argv: list[str]
    notes: str = ""
    safe: bool = True  # True → catch_exceptions=False (fail fast on bugs)


@dataclass(slots=True)
class CaptureResult:
    """Outcome of a single CLI capture invocation."""

    section: str
    title: str
    argv: list[str]
    argv_base: list[str]
    exit_code: int
    elapsed_seconds: float
    stdout_full: str
    truncated: bool = False
    # Format variants (populated only for commands that produce API JSON).
    stdout_json: str | None = None
    stdout_yaml: str | None = None
    stdout_markdown: str | None = None

    @property
    def is_config_error(self) -> bool:
        """True if the command failed due to missing configuration."""
        return any(sig in self.stdout_full for sig in CONFIG_ERROR_SIGNALS)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON storage."""
        d: dict[str, Any] = {
            "section": self.section,
            "title": self.title,
            "argv": list(self.argv),
            "argv_base": list(self.argv_base),
            "exit_code": self.exit_code,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "truncated": self.truncated,
            "stdout_full": self.stdout_full,
        }
        if self.stdout_json is not None:
            d["stdout_json"] = self.stdout_json
        if self.stdout_yaml is not None:
            d["stdout_yaml"] = self.stdout_yaml
        if self.stdout_markdown is not None:
            d["stdout_markdown"] = self.stdout_markdown
        return d


@dataclass(slots=True)
class CaptureArtifact:
    """A successfully captured result ready for file output."""

    result: CaptureResult
    filename: str  # e.g. "046-live-api-demo-…-devices-list.json"


# ── Utility functions ────────────────────────────────────────────────────────


def supports_format_variants(argv: list[str]) -> bool:
    """Return True if *argv* represents a command that produces API JSON.

    Help-only commands, schema-discovery, and static local commands
    produce plain text — re-running them with ``--json`` would yield
    invalid JSON and is therefore skipped.
    """
    if "--help" in argv:
        return False
    if any(f in argv for f in _OUTPUT_FORMAT_FLAGS):
        return False
    if argv and argv[0] in _LOCAL_COMMANDS:
        return False
    return True


def strip_status_header(text: str) -> str:
    """Remove the ``Status: NNN`` header added by ``print_response``."""
    return _STATUS_HEADER_RE.sub("", text, count=1)


def truncate(text: str, max_lines: int, max_chars: int) -> tuple[str, bool]:
    """Truncate *text* and return ``(truncated_text, was_truncated)``."""
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n\u2026 (truncated by character limit)\n", True
    lines = text.splitlines()
    if len(lines) > max_lines:
        head = "\n".join(lines[:max_lines])
        return head + f"\n\n\u2026 ({len(lines) - max_lines} more lines truncated)\n", True
    return text, False


def build_slug(section: str, title: str, max_len: int = 80) -> str:
    """Create a filesystem-safe slug from section + title."""
    raw = f"{section}-{title}"[:max_len].lower().replace(" ", "-").replace("/", "-")
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in raw)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug


def inject_format_flag(argv: list[str], flag: str) -> list[str]:
    """Return *argv* with *flag* appended, replacing any existing format flag."""
    clean = [a for a in argv if a not in _OUTPUT_FORMAT_FLAGS]
    return [*clean, flag]
