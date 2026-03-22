"""MkDocs hook: generate docs/reference/command-examples.md from captured JSON artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RAW_DIR = _REPO_ROOT / "docs" / "generated" / "raw"
_INDEX_FILE = _RAW_DIR / "index.json"
_OUTPUT_FILE = _REPO_ROOT / "docs" / "reference" / "command-examples.md"


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences so terminal output renders cleanly in Markdown."""
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def _badge(exit_code: int) -> str:
    if exit_code == 0:
        return '<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span>'
    return f'<span class="nbx-badge nbx-badge--err">exit&nbsp;{exit_code}</span>'


def _duration_badge(seconds: float) -> str:
    return f'<span class="nbx-badge nbx-badge--neutral">{seconds:.3f}s</span>'


def _build_command_examples() -> str:
    """Read all raw JSON captures and produce a rich Material Markdown page."""
    if not _INDEX_FILE.exists():
        return (
            "# Command Examples\n\n"
            '!!! warning "Not yet generated"\n'
            "    Run `nbx docs generate-capture` from the repo root to generate "
            "command capture artifacts, then rebuild the docs.\n"
        )

    index = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
    meta = index.get("meta", {})
    runs = index.get("runs", [])

    generated_at = meta.get("generated_at", "unknown")
    profile = meta.get("profile", "demo")
    netbox_url = meta.get("netbox_url", "https://demo.netbox.dev")
    token_ok = meta.get("token_configured", False)

    # Build a lookup from (section, title) → full stdout
    raw_files = sorted(_RAW_DIR.glob("*.json"))
    stdout_map: dict[tuple[str, str], str] = {}
    for f in raw_files:
        if f.name == "index.json":
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            key = (d.get("section", ""), d.get("title", ""))
            stdout_map[key] = _strip_ansi(d.get("stdout_full", ""))
        except (json.JSONDecodeError, KeyError):
            continue

    lines: list[str] = [
        "# Command Examples",
        "",
        '!!! info "Machine-generated"',
        "    This page is automatically generated from CLI captures.",
        f"    Last updated: `{generated_at}`",
        "",
        '??? note "Generation metadata"',
        "    | Key | Value |",
        "    |-----|-------|",
        f"    | Profile | `{profile}` |",
        f"    | NetBox URL | `{netbox_url}` |",
        f"    | Token configured | `{token_ok}` |",
        f"    | Commands captured | `{len(runs)}` |",
        "",
        "---",
        "",
    ]

    section_last = ""
    for i, run in enumerate(runs):
        section = run.get("section", "")
        title = run.get("title", "")
        argv = run.get("argv", [])
        exit_code = run.get("exit_code", 0)
        elapsed = run.get("elapsed_seconds", 0.0)
        truncated = run.get("truncated", False)

        if section != section_last:
            if section_last:
                lines.append("")
            lines.append(f"## {section}")
            lines.append("")
            section_last = section

        stdout = stdout_map.get((section, title), "").rstrip()

        cmd = "nbx " + " ".join(argv)

        lines.append(f"### `{title}`")
        lines.append("")
        lines.append('=== ":material-console: Command"')
        lines.append("")
        lines.append("    ```bash")
        lines.append(f"    {cmd}")
        lines.append("    ```")
        lines.append("")
        lines.append('=== ":material-text-box-outline: Output"')
        lines.append("")
        lines.append("    ```text")
        for out_line in (stdout or "(empty)").splitlines():
            lines.append(f"    {out_line}")
        lines.append("    ```")
        lines.append("")

        # Status line
        badge_exit = _badge(exit_code)
        badge_dur = _duration_badge(elapsed)
        lines.append(f"{badge_exit} {badge_dur}")

        if truncated:
            lines.append("")
            lines.append(
                '!!! warning "Truncated"'
                "\n    Output was truncated. Full text is in `docs/generated/raw/`."
            )

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def on_pre_build(config, **kwargs) -> None:
    """Generate the command examples page before MkDocs processes any files."""
    _OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = _build_command_examples()
    _OUTPUT_FILE.write_text(content, encoding="utf-8")
