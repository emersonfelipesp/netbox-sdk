"""MkDocs hook: generate docs/reference/command-examples/ from captured JSON artifacts.

One Markdown file is generated per section (e.g. ``top-level.md``, ``schema-discovery.md``).
An ``index.md`` overview page is also written with links to every section.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RAW_DIR = _REPO_ROOT / "docs" / "generated" / "raw"
_INDEX_FILE = _RAW_DIR / "index.json"
_OUTPUT_DIR = _REPO_ROOT / "docs" / "reference" / "command-examples"


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences so terminal output renders cleanly in Markdown."""
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def _slug(section: str) -> str:
    """Convert a section name to a URL-safe filename slug."""
    s = section.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _badge(exit_code: int) -> str:
    if exit_code == 0:
        return '<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span>'
    return f'<span class="nbx-badge nbx-badge--err">exit&nbsp;{exit_code}</span>'


def _duration_badge(seconds: float) -> str:
    return f'<span class="nbx-badge nbx-badge--neutral">{seconds:.3f}s</span>'


def _render_section(
    section: str,
    runs: list[dict],
    stdout_map: dict[tuple[str, str], str],
) -> str:
    """Render a single section as a Markdown page."""
    lines: list[str] = [
        f"# {section}",
        "",
    ]

    for run in runs:
        title = run.get("title", "")
        argv = run.get("argv", [])
        exit_code = run.get("exit_code", 0)
        elapsed = run.get("elapsed_seconds", 0.0)
        truncated = run.get("truncated", False)
        notes = run.get("notes", "")

        stdout = stdout_map.get((section, title), "").rstrip()
        cmd = "nbx " + " ".join(argv)

        lines.append(f"### `{title}`")
        lines.append("")

        if notes:
            lines.append('!!! note ""')
            lines.append(f"    {notes}")
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


def _not_generated_index() -> str:
    return (
        "# Command Examples\n\n"
        '!!! warning "Not yet generated"\n'
        "    Run `nbx docs generate-capture` from the repo root to generate "
        "command capture artifacts, then rebuild the docs.\n"
    )


def _build_command_examples() -> None:
    """Read all raw JSON captures and produce one Markdown file per section."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not _INDEX_FILE.exists():
        (_OUTPUT_DIR / "index.md").write_text(_not_generated_index(), encoding="utf-8")
        return

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

    # Group runs by section (preserve insertion order)
    sections: dict[str, list[dict]] = {}
    for run in runs:
        sec = run.get("section", "Uncategorized")
        sections.setdefault(sec, []).append(run)

    # Write one file per section
    section_slugs: list[tuple[str, str]] = []  # (section_name, slug)
    for section, section_runs in sections.items():
        slug = _slug(section)
        content = _render_section(section, section_runs, stdout_map)
        (_OUTPUT_DIR / f"{slug}.md").write_text(content, encoding="utf-8")
        section_slugs.append((section, slug))

    # Write index page
    index_lines: list[str] = [
        "# Command Examples",
        "",
        '!!! info "Machine-generated"',
        "    These pages are automatically generated from CLI captures.",
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
        "## Sections",
        "",
    ]
    for section_name, slug in section_slugs:
        count = len(sections[section_name])
        index_lines.append(
            f"- [{section_name}](./{slug}.md) — {count} command{'s' if count != 1 else ''}"
        )
    index_lines.append("")

    (_OUTPUT_DIR / "index.md").write_text("\n".join(index_lines), encoding="utf-8")


def on_pre_build(config, **kwargs) -> None:
    """Generate the command examples pages before MkDocs processes any files."""
    _build_command_examples()
