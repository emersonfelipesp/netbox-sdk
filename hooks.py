"""MkDocs hook: generate surface-specific reference pages from captured JSON artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_RAW_DIR = _REPO_ROOT / "docs" / "generated" / "raw"
_INDEX_FILE = _RAW_DIR / "index.json"

_SURFACE_OUTPUTS = {
    "cli": {
        "title": "CLI Command Output",
        "description": (
            "Captured help banners, schema discovery, demo-backed resource commands, "
            "and developer-tool output for the `netbox_cli` package."
        ),
        "output_dir": _REPO_ROOT / "docs" / "reference" / "cli" / "command-examples",
    },
    "tui": {
        "title": "TUI Launch Output",
        "description": (
            "Captured launch, help, and theme-selection output for the `netbox_tui` package."
        ),
        "output_dir": _REPO_ROOT / "docs" / "reference" / "tui" / "launch-examples",
    },
}


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def _slug(label: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", label.lower())
    return value.strip("-")


def _badge(exit_code: int) -> str:
    if exit_code == 0:
        return '<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span>'
    return f'<span class="nbx-badge nbx-badge--err">exit&nbsp;{exit_code}</span>'


def _duration_badge(seconds: float) -> str:
    return f'<span class="nbx-badge nbx-badge--neutral">{seconds:.3f}s</span>'


def _write_placeholder_indexes() -> None:
    for meta in _SURFACE_OUTPUTS.values():
        output_dir = meta["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.md").write_text(
            "\n".join(
                [
                    f"# {meta['title']}",
                    "",
                    '!!! warning "Not yet generated"',
                    "    Run `nbx docs generate-capture` from the repo root, then rebuild the docs.",
                    "",
                    meta["description"],
                    "",
                ]
            ),
            encoding="utf-8",
        )


def _render_section(section: str, runs: list[dict], stdout_map: dict[tuple[str, str, str], dict]) -> str:
    lines: list[str] = [f"# {section}", ""]

    for run in runs:
        surface = run.get("surface", "cli")
        title = run.get("title", "")
        argv = run.get("argv", [])
        argv_base = run.get("argv_base", argv)
        exit_code = run.get("exit_code", 0)
        elapsed = run.get("elapsed_seconds", 0.0)
        notes = run.get("notes", "")

        data = stdout_map.get((surface, section, title), {})
        stdout = (data.get("stdout_full") or "(empty)").rstrip()
        stdout_json = data.get("stdout_json")
        stdout_yaml = data.get("stdout_yaml")
        stdout_md = data.get("stdout_markdown")

        cmd_base = "nbx " + " ".join(argv_base)
        cmd_json = "nbx " + " ".join(argv_base + ["--json"])
        cmd_yaml = "nbx " + " ".join(argv_base + ["--yaml"])
        cmd_markdown = "nbx " + " ".join(argv)

        lines.append(f"## `{title}`")
        lines.append("")

        if notes:
            lines.append('!!! note ""')
            lines.append(f"    {notes}")
            lines.append("")

        lines.append('=== ":material-console: Command"')
        lines.append("")
        lines.append("    ```bash")
        lines.append(f"    {cmd_base}")
        lines.append("    ```")
        lines.append("")

        lines.append('=== ":material-text-box-outline: Output"')
        lines.append("")
        lines.append("    ```bash")
        lines.append(f"    {cmd_base}")
        lines.append("    ```")
        lines.append("")
        lines.append("    ```text")
        for out_line in stdout.splitlines():
            lines.append(f"    {out_line}")
        lines.append("    ```")
        lines.append("")

        if stdout_json:
            lines.append('=== ":material-code-json: JSON Output"')
            lines.append("")
            lines.append("    ```bash")
            lines.append(f"    {cmd_json}")
            lines.append("    ```")
            lines.append("")
            lines.append("    ```json")
            for json_line in stdout_json.splitlines():
                lines.append(f"    {json_line}")
            lines.append("    ```")
            lines.append("")

        if stdout_yaml:
            lines.append('=== ":material-file-document-outline: YAML Output"')
            lines.append("")
            lines.append("    ```bash")
            lines.append(f"    {cmd_yaml}")
            lines.append("    ```")
            lines.append("")
            lines.append("    ```yaml")
            for yaml_line in stdout_yaml.splitlines():
                lines.append(f"    {yaml_line}")
            lines.append("    ```")
            lines.append("")

        if stdout_md:
            lines.append('=== ":material-language-markdown: Markdown Output"')
            lines.append("")
            lines.append("    ```bash")
            lines.append(f"    {cmd_markdown}")
            lines.append("    ```")
            lines.append("")
            for md_line in stdout_md.splitlines():
                lines.append(f"    {md_line}")
            lines.append("")

        lines.append(f"{_badge(exit_code)} {_duration_badge(elapsed)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _surface_intro(surface: str) -> str:
    if surface == "cli":
        return (
            "These captures document the `netbox_cli` package. Any command that talks to "
            "a live NetBox instance is shown in its demo-safe form as `nbx demo ...`."
        )
    return (
        "These captures document the `netbox_tui` package launch surface. They cover "
        "help banners and theme selection without embedding screenshots."
    )


def _write_surface_index(
    surface: str,
    meta: dict,
    sections: dict[str, list[dict]],
    section_slugs: list[tuple[str, str]],
) -> None:
    surface_meta = _SURFACE_OUTPUTS[surface]
    index_lines: list[str] = [
        f"# {surface_meta['title']}",
        "",
        surface_meta["description"],
        "",
        _surface_intro(surface),
        "",
        '!!! info "Machine-generated"',
        "    These pages are generated from the command-capture artifacts.",
        f"    Last updated: `{meta.get('generated_at', 'unknown')}`",
        "",
        '??? note "Generation metadata"',
        "    | Key | Value |",
        "    |-----|-------|",
        f"    | Profile | `{meta.get('profile', 'demo')}` |",
        f"    | NetBox URL | `{meta.get('netbox_url', 'https://demo.netbox.dev')}` |",
        f"    | Token configured | `{meta.get('token_configured', False)}` |",
        f"    | Commands captured | `{sum(len(items) for items in sections.values())}` |",
        "",
        "## Sections",
        "",
    ]
    for section_name, slug in section_slugs:
        count = len(sections[section_name])
        index_lines.append(f"- [{section_name}](./{slug}.md) — {count} captures")
    index_lines.append("")

    output_dir = surface_meta["output_dir"]
    (output_dir / "index.md").write_text("\n".join(index_lines), encoding="utf-8")


def _build_command_examples() -> None:
    for meta in _SURFACE_OUTPUTS.values():
        output_dir = meta["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

    if not _INDEX_FILE.exists():
        _write_placeholder_indexes()
        return

    index = json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
    meta = index.get("meta", {})
    runs = index.get("runs", [])

    stdout_map: dict[tuple[str, str, str], dict] = {}
    for artifact in sorted(_RAW_DIR.glob("*.json")):
        if artifact.name == "index.json":
            continue
        try:
            data = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        key = (data.get("surface", "cli"), data.get("section", ""), data.get("title", ""))
        stdout_map[key] = {
            "stdout_full": _strip_ansi(data.get("stdout_full", "")),
            "stdout_json": data.get("stdout_json"),
            "stdout_yaml": data.get("stdout_yaml"),
            "stdout_markdown": data.get("stdout_markdown"),
        }

    grouped: dict[str, dict[str, list[dict]]] = {surface: {} for surface in _SURFACE_OUTPUTS}
    for run in runs:
        surface = run.get("surface", "cli")
        if surface not in grouped:
            continue
        section = run.get("section", "Uncategorized")
        grouped[surface].setdefault(section, []).append(run)

    for surface, sections in grouped.items():
        output_dir = _SURFACE_OUTPUTS[surface]["output_dir"]
        section_slugs: list[tuple[str, str]] = []
        for section, section_runs in sections.items():
            slug = _slug(section)
            (output_dir / f"{slug}.md").write_text(
                _render_section(section, section_runs, stdout_map),
                encoding="utf-8",
            )
            section_slugs.append((section, slug))
        _write_surface_index(surface, meta, sections, section_slugs)


def on_pre_build(config, **kwargs) -> None:
    _build_command_examples()
