"""MkDocs hook: generate surface-specific reference pages from captured JSON artifacts."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Markdown uses /assets/... so `mkdocs build --strict` accepts image targets (root-absolute
# links are not validated like doc-relative paths). mkdocs-static-i18n non-default locales
# output under `site/<locale>/` while static assets stay under `site/assets/`, so literal
# `/assets/...` would 404; rewrite after the template pass to a path relative to each page.
_IMG_SRC_ABS_ASSETS = re.compile(r'src="/assets/([^"]+)"')


def _site_assets_root(config) -> Path:
    site_dir = Path(config.site_dir).resolve()
    if (site_dir / "assets").is_dir():
        return site_dir / "assets"
    parent = site_dir.parent / "assets"
    if parent.is_dir():
        return parent
    return site_dir / "assets"


def _rewrite_img_src_abs_assets(output: str, page, config) -> str:
    page_dir = Path(page.file.abs_dest_path).resolve().parent
    assets_root = _site_assets_root(config)

    def repl(match: re.Match[str]) -> str:
        rel_asset = match.group(1)
        target = (assets_root / rel_asset).resolve()
        try:
            rel = os.path.relpath(target, page_dir).replace(os.sep, "/")
        except ValueError:
            return match.group(0)
        return f'src="{rel}"'

    return _IMG_SRC_ABS_ASSETS.sub(repl, output)


_RAW_DIR = _REPO_ROOT / "docs" / "generated" / "raw"
_INDEX_FILE = _RAW_DIR / "index.json"

_SURFACE_OUTPUTS = {
    "cli": {
        "title": {
            "en": "CLI Command Output",
            "pt": "Saída de comandos da CLI",
        },
        "description": {
            "en": (
                "Captured help banners, schema discovery, demo-backed resource commands, "
                "and developer-tool output for the `netbox_cli` package."
            ),
            "pt": (
                "Capturas de banners de ajuda, descoberta de esquema, comandos de recursos "
                "com perfil demo e saída de ferramentas de desenvolvimento do pacote `netbox_cli`."
            ),
        },
        "output_dir": _REPO_ROOT / "docs" / "reference" / "cli" / "command-examples",
    },
    "tui": {
        "title": {
            "en": "TUI Launch Output",
            "pt": "Saída de lançamento da TUI",
        },
        "description": {
            "en": (
                "Captured launch, help, and theme-selection output for the `netbox_tui` package."
            ),
            "pt": ("Capturas de lançamento, ajuda e seleção de tema do pacote `netbox_tui`."),
        },
        "output_dir": _REPO_ROOT / "docs" / "reference" / "tui" / "launch-examples",
    },
}

_UI = {
    "en": {
        "placeholder_warning_title": "Not yet generated",
        "placeholder_warning_body": (
            "Run `nbx docs generate-capture` from the repo root, then rebuild the docs."
        ),
        "tab_command": "Command",
        "tab_output": "Output",
        "tab_json": "JSON Output",
        "tab_yaml": "YAML Output",
        "tab_markdown": "Markdown Output",
        "badge_exit_ok": "exit&nbsp;0",
        "badge_exit_err": "exit&nbsp;{code}",
        "intro_cli": (
            "These captures document the `netbox_cli` package. Any command that talks to "
            "a live NetBox instance is shown in its demo-safe form as `nbx demo ...`."
        ),
        "intro_tui": (
            "These captures document the `netbox_tui` package launch surface. They cover "
            "help banners and theme selection without embedding screenshots."
        ),
        "info_machine_title": "Machine-generated",
        "info_machine_body": "These pages are generated from the command-capture artifacts.",
        "info_last_updated": "Last updated:",
        "meta_note_title": "Generation metadata",
        "meta_key": "Key",
        "meta_value": "Value",
        "meta_profile": "Profile",
        "meta_netbox_url": "NetBox URL",
        "meta_token": "Token configured",
        "meta_commands": "Commands captured",
        "sections_heading": "Sections",
        "captures_suffix": "captures",
        "section_index_sep": "—",
    },
    "pt": {
        "placeholder_warning_title": "Ainda não gerado",
        "placeholder_warning_body": (
            "Execute `nbx docs generate-capture` na raiz do repositório e reconstrua a documentação."
        ),
        "tab_command": "Comando",
        "tab_output": "Saída",
        "tab_json": "Saída JSON",
        "tab_yaml": "Saída YAML",
        "tab_markdown": "Saída Markdown",
        "badge_exit_ok": "saída&nbsp;0",
        "badge_exit_err": "saída&nbsp;{code}",
        "intro_cli": (
            "Estas capturas documentam o pacote `netbox_cli`. Qualquer comando que fale com "
            "uma instância NetBox ao vivo aparece na forma segura para demo como `nbx demo ...`."
        ),
        "intro_tui": (
            "Estas capturas documentam a superfície de lançamento do pacote `netbox_tui`. "
            "Incluem banners de ajuda e seleção de tema, sem incorporar capturas de tela."
        ),
        "info_machine_title": "Gerado automaticamente",
        "info_machine_body": "Estas páginas são geradas a partir dos artefatos de captura de comandos.",
        "info_last_updated": "Última atualização:",
        "meta_note_title": "Metadados de geração",
        "meta_key": "Chave",
        "meta_value": "Valor",
        "meta_profile": "Perfil",
        "meta_netbox_url": "URL do NetBox",
        "meta_token": "Token configurado",
        "meta_commands": "Comandos capturados",
        "sections_heading": "Seções",
        "captures_suffix": "capturas",
        "section_index_sep": "—",
    },
}


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def _slug(label: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", label.lower())
    return value.strip("-")


def _badge(exit_code: int, lang: str) -> str:
    ui = _UI[lang]
    if exit_code == 0:
        return f'<span class="nbx-badge nbx-badge--ok">{ui["badge_exit_ok"]}</span>'
    err = ui["badge_exit_err"].format(code=exit_code)
    return f'<span class="nbx-badge nbx-badge--err">{err}</span>'


def _duration_badge(seconds: float) -> str:
    return f'<span class="nbx-badge nbx-badge--neutral">{seconds:.3f}s</span>'


def _write_placeholder_indexes() -> None:
    for surface_meta in _SURFACE_OUTPUTS.values():
        output_dir = surface_meta["output_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)
        for lang in ("en", "pt"):
            ui = _UI[lang]
            title = surface_meta["title"][lang]
            desc = surface_meta["description"][lang]
            suffix = "" if lang == "en" else ".pt"
            (output_dir / f"index{suffix}.md").write_text(
                "\n".join(
                    [
                        f"# {title}",
                        "",
                        f'!!! warning "{ui["placeholder_warning_title"]}"',
                        f"    {ui['placeholder_warning_body']}",
                        "",
                        desc,
                        "",
                    ]
                ),
                encoding="utf-8",
            )


def _render_section(
    section: str,
    runs: list[dict],
    stdout_map: dict[tuple[str, str, str], dict],
    lang: str,
) -> str:
    ui = _UI[lang]
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

        lines.append(f'=== ":material-console: {ui["tab_command"]}"')
        lines.append("")
        lines.append("    ```bash")
        lines.append(f"    {cmd_base}")
        lines.append("    ```")
        lines.append("")

        lines.append(f'=== ":material-text-box-outline: {ui["tab_output"]}"')
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
            lines.append(f'=== ":material-code-json: {ui["tab_json"]}"')
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
            lines.append(f'=== ":material-file-document-outline: {ui["tab_yaml"]}"')
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
            lines.append(f'=== ":material-language-markdown: {ui["tab_markdown"]}"')
            lines.append("")
            lines.append("    ```bash")
            lines.append(f"    {cmd_markdown}")
            lines.append("    ```")
            lines.append("")
            for md_line in stdout_md.splitlines():
                lines.append(f"    {md_line}")
            lines.append("")

        lines.append(f"{_badge(exit_code, lang)} {_duration_badge(elapsed)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _surface_intro(surface: str, lang: str) -> str:
    ui = _UI[lang]
    return ui["intro_cli"] if surface == "cli" else ui["intro_tui"]


def _write_surface_index(
    surface: str,
    meta: dict,
    sections: dict[str, list[dict]],
    section_slugs: list[tuple[str, str]],
    lang: str,
) -> None:
    surface_meta = _SURFACE_OUTPUTS[surface]
    ui = _UI[lang]
    title = surface_meta["title"][lang]
    description = surface_meta["description"][lang]
    sep = ui["section_index_sep"]
    cap = ui["captures_suffix"]
    index_lines: list[str] = [
        f"# {title}",
        "",
        description,
        "",
        _surface_intro(surface, lang),
        "",
        f'!!! info "{ui["info_machine_title"]}"',
        f"    {ui['info_machine_body']}",
        f"    {ui['info_last_updated']} `{meta.get('generated_at', 'unknown')}`",
        "",
        f'??? note "{ui["meta_note_title"]}"',
        f"    | {ui['meta_key']} | {ui['meta_value']} |",
        "    |-----|-------|",
        f"    | {ui['meta_profile']} | `{meta.get('profile', 'demo')}` |",
        f"    | {ui['meta_netbox_url']} | `{meta.get('netbox_url', 'https://demo.netbox.dev')}` |",
        f"    | {ui['meta_token']} | `{meta.get('token_configured', False)}` |",
        f"    | {ui['meta_commands']} | `{sum(len(items) for items in sections.values())}` |",
        "",
        f"## {ui['sections_heading']}",
        "",
    ]
    for section_name, slug in section_slugs:
        count = len(sections[section_name])
        index_lines.append(f"- [{section_name}](./{slug}.md) {sep} {count} {cap}")
    index_lines.append("")

    output_dir = surface_meta["output_dir"]
    suffix = "" if lang == "en" else ".pt"
    (output_dir / f"index{suffix}.md").write_text("\n".join(index_lines), encoding="utf-8")


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
                _render_section(section, section_runs, stdout_map, "en"),
                encoding="utf-8",
            )
            (output_dir / f"{slug}.pt.md").write_text(
                _render_section(section, section_runs, stdout_map, "pt"),
                encoding="utf-8",
            )
            section_slugs.append((section, slug))
        _write_surface_index(surface, meta, sections, section_slugs, "en")
        _write_surface_index(surface, meta, sections, section_slugs, "pt")


def on_pre_build(config, **kwargs) -> None:
    _build_command_examples()


def on_post_page(output: str, *, page, config, **kwargs) -> str:
    _ = kwargs
    if 'src="/assets/' not in output:
        return output
    return _rewrite_img_src_abs_assets(output, page, config)
