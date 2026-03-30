"""Backward-compatible facade for the docgen capture pipeline.

Public API (preserved):
    ``generate_command_capture_docs()``  — main entry point
    ``resolve_capture_paths()``          — path resolution
    ``argv_with_markdown_output()``      — flag injection helper

Internal implementation delegates to ``netbox_cli.docgen`` sub-package.

Documentation guidelines (AGENTS):
- All captured output MUST come from demo.netbox.dev only.  Never use a
  production instance to generate docs — it will leak customer data.
- Commands that fail with configuration errors (interactive prompts, aborted)
  are skipped and never included in final output.
- Each command gets tabs: Command, Output (human), JSON Output, YAML Output,
  Markdown Output.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from netbox_cli.docgen.engine import CaptureEngine
from netbox_cli.docgen.models import (
    DEFAULT_MAX_CONCURRENCY,
    CaptureResult,
)
from netbox_cli.docgen.specs import load_specs

# Re-exported for tests that import from this module.
from netbox_cli.docgen_specs import CaptureSpec as CaptureSpec  # noqa: F401

# OpenAPI dynamic actions that render via ``print_response`` (tabular / Markdown-friendly).
_MARKDOWN_ACTIONS = frozenset({"list", "get", "create", "update", "patch", "delete"})
_OUTPUT_FORMAT_FLAGS = frozenset({"--json", "--yaml", "--markdown"})


# ── Public helpers ──────────────────────────────────────────────────────────


def argv_with_markdown_output(argv: list[str], *, enabled: bool) -> list[str]:
    """Return argv, appending ``--markdown`` when doc capture should use Markdown tables.

    Skips ``--help``, leaves argv unchanged when ``--json`` / ``--yaml`` / ``--markdown``
    is already present, and only targets ``call`` plus dynamic
    ``[<demo>] <group> <resource> <action>`` invocations.
    """
    if not enabled:
        return list(argv)
    if "--help" in argv:
        return list(argv)
    if any(t in _OUTPUT_FORMAT_FLAGS for t in argv):
        return list(argv)

    opt_idx = next((i for i, t in enumerate(argv) if t.startswith("-")), len(argv))
    pos = argv[:opt_idx]
    if not pos:
        return list(argv)

    if pos[0] == "call" and len(pos) >= 3:
        return [*argv, "--markdown"]

    body = pos[1:] if pos[0] == "demo" else pos
    if len(body) >= 3 and body[-1] in _MARKDOWN_ACTIONS:
        return [*argv, "--markdown"]

    return list(argv)


def resolve_capture_paths(
    output: Path | None,
    raw_dir: Path | None,
) -> tuple[Path, Path]:
    """Default under ``<repo>/docs/generated/`` when the repo layout is present."""
    docs_dir = _repo_root() / "docs"
    default_out = docs_dir / "generated" / "nbx-command-capture.md"
    if not docs_dir.is_dir():
        if output is None or raw_dir is None:
            raise FileNotFoundError(
                "Cannot infer default paths: no docs/ directory next to netbox_cli. "
                "Run from the netbox-sdk git checkout or pass --output and --raw-dir."
            )
        return output, raw_dir
    if output is None:
        output = default_out
    if raw_dir is None:
        raw_dir = output.parent / "raw"
    return output, raw_dir


# ── Main entry point ────────────────────────────────────────────────────────


def generate_command_capture_docs(
    *,
    output: Path,
    raw_dir: Path,
    markdown_output: bool = True,
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
    log: TextIO | None = None,
) -> int:
    """Write capture Markdown and raw JSON artifacts.  Returns 0 on success.

    Args:
        max_concurrency: Max parallel CLI captures (default 4).
            Set to 1 for fully sequential execution.
    """
    log = log or sys.stderr
    profile = "demo"

    output.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ── Resolve metadata ──────────────────────────────────────────────────
    meta = _build_meta(markdown_output)

    # ── Load specs and run capture engine ──────────────────────────────────
    specs = load_specs()

    engine = CaptureEngine(
        max_concurrency=max_concurrency,
        markdown_output=markdown_output,
        log=log,
    )

    results = engine.capture_all(specs, profile=profile)

    # ── Separate skipped from valid results ───────────────────────────────
    valid: list[CaptureResult] = []
    skipped: list[str] = []
    for r in results:
        if r.is_config_error:
            skipped.append(r.title)
            print(f"  SKIPPED (config error): {r.title}", file=log)
        else:
            valid.append(r)

    # ── Remove stale JSON artifacts, then write fresh ones ───────────────
    for existing in raw_dir.glob("*.json"):
        existing.unlink()

    engine.write_artifacts(valid, raw_dir)

    # ── Write Markdown capture file (EN default + PT mirror) ───────────────
    md_text = _render_markdown_capture(meta, valid)
    output.write_text(md_text, encoding="utf-8")
    pt_path = output.with_name(f"{output.stem}.pt{output.suffix}")
    pt_path.write_text(_render_markdown_capture_pt(meta, valid), encoding="utf-8")

    # ── Write index.json for the MkDocs hook ──────────────────────────────
    index_data = {
        "meta": meta,
        "runs": [r.to_dict() for r in valid],
    }
    (raw_dir / "index.json").write_text(
        json.dumps(index_data, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote {output} and {pt_path}", file=log)
    print(f"Wrote {len(valid)} raw JSON files under {raw_dir}", file=log)
    if skipped:
        print(f"Skipped {len(skipped)} commands (config errors): {skipped}", file=log)
    return 0


# ── Private helpers ─────────────────────────────────────────────────────────


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _build_meta(markdown_output: bool) -> dict:
    from netbox_sdk.config import DEMO_BASE_URL, load_profile_config  # noqa: PLC0415

    profile = "demo"
    cfg = load_profile_config(profile)
    effective_url = cfg.base_url or DEMO_BASE_URL
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "profile": profile,
        "netbox_url": effective_url,
        "timeout": os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"),
        "token_configured": bool(cfg.token_key and cfg.token_secret),
        "markdown_output": markdown_output,
    }


def _render_markdown_capture(
    meta: dict,
    results: list[CaptureResult],
) -> str:
    """Render the human-readable Markdown capture file."""
    profile_note = "**demo profile** (`nbx demo ...` commands -> demo.netbox.dev)"

    lines: list[str] = [
        "# netbox-sdk \u2014 captured command input and output",
        "",
        "This file is **machine-generated**. Regenerate with:",
        "",
        "```bash",
        "cd /path/to/netbox-sdk",
        "uv sync --group docs --group dev   # once",
        "uv run nbx docs generate-capture",
        "# or: uv run python docs/generate_command_docs.py",
        "```",
        "",
        "Run the capture **in the background** (log + pid):",
        "",
        "```bash",
        "./docs/run_capture_in_background.sh",
        "```",
        "",
        "## Generation metadata",
        "",
        f"- **UTC time:** `{meta['generated_at']}`",
        f"- **Profile used:** {profile_note}",
        f"- **Effective NetBox URL:** `{meta['netbox_url']}`",
        f"- **Effective timeout (s):** `{meta['timeout']}`",
        f"- **Token configured:** `{meta['token_configured']}`",
        "",
        (
            "> Docgen is restricted to the demo profile only. Any live data shown here "
            "comes from demo.netbox.dev, never from a production NetBox instance."
        ),
        "",
        (
            "> **Typer `CliRunner` quirk:** help banners may show `Usage: root` instead of "
            "`Usage: nbx`. The installed `nbx` script uses the correct name."
        ),
        "",
        "---",
        "",
    ]

    surface_last = ""
    section_last = ""
    for r in results:
        if r.surface != surface_last:
            lines.append(f"## {r.surface.upper()}")
            lines.append("")
            surface_last = r.surface
            section_last = ""
        if r.section != section_last:
            lines.append(f"### {r.section}")
            lines.append("")
            section_last = r.section

        cmd_display = "nbx " + " ".join(r.argv)
        lines.append(f"#### {r.title}")
        lines.append("")
        lines.append("**Input:**")
        lines.append("")
        lines.append("```bash")
        lines.append(cmd_display)
        lines.append("```")
        lines.append("")
        lines.append(
            f"**Exit code:** `{r.exit_code}`  \u00b7  **Wall time (s):** `{r.elapsed_seconds:.3f}`"
        )
        lines.append("")
        lines.append("**Output:**")
        lines.append("")
        lines.append("```text")
        lines.append(r.stdout_full.rstrip() or "(empty)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def _render_markdown_capture_pt(
    meta: dict,
    results: list[CaptureResult],
) -> str:
    """Portuguese mirror of `_render_markdown_capture` (terminal output unchanged)."""
    profile_note = "**perfil demo** (comandos `nbx demo ...` → demo.netbox.dev)"

    lines: list[str] = [
        "# netbox-sdk — entrada e saída de comandos capturados",
        "",
        "Este arquivo é **gerado automaticamente**. Para regenerar:",
        "",
        "```bash",
        "cd /path/to/netbox-sdk",
        "uv sync --group docs --group dev   # uma vez",
        "uv run nbx docs generate-capture",
        "# ou: uv run python docs/generate_command_docs.py",
        "```",
        "",
        "Execute a captura **em segundo plano** (log + pid):",
        "",
        "```bash",
        "./docs/run_capture_in_background.sh",
        "```",
        "",
        "## Metadados de geração",
        "",
        f"- **Hora UTC:** `{meta['generated_at']}`",
        f"- **Perfil usado:** {profile_note}",
        f"- **URL efetiva do NetBox:** `{meta['netbox_url']}`",
        f"- **Timeout efetivo (s):** `{meta['timeout']}`",
        f"- **Token configurado:** `{meta['token_configured']}`",
        "",
        (
            "> A geração de documentação está restrita ao perfil demo. Qualquer dado ao vivo "
            "mostrado aqui vem de demo.netbox.dev, nunca de uma instância NetBox de produção."
        ),
        "",
        (
            "> **Comportamento do Typer `CliRunner`:** os banners de ajuda podem mostrar "
            "`Usage: root` em vez de `Usage: nbx`. O script instalado `nbx` usa o nome correto."
        ),
        "",
        "---",
        "",
    ]

    surface_last = ""
    section_last = ""
    for r in results:
        if r.surface != surface_last:
            lines.append(f"## {r.surface.upper()}")
            lines.append("")
            surface_last = r.surface
            section_last = ""
        if r.section != section_last:
            lines.append(f"### {r.section}")
            lines.append("")
            section_last = r.section

        cmd_display = "nbx " + " ".join(r.argv)
        lines.append(f"#### {r.title}")
        lines.append("")
        lines.append("**Entrada:**")
        lines.append("")
        lines.append("```bash")
        lines.append(cmd_display)
        lines.append("```")
        lines.append("")
        lines.append(
            f"**Código de saída:** `{r.exit_code}`  ·  **Tempo de parede (s):** "
            f"`{r.elapsed_seconds:.3f}`"
        )
        lines.append("")
        lines.append("**Saída:**")
        lines.append("")
        lines.append("```text")
        lines.append(r.stdout_full.rstrip() or "(vazio)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)
