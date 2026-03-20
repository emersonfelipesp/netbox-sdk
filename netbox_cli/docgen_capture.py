"""Generate Markdown + JSON capturing `nbx` CLI invocations (Typer CliRunner)."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from inspect import signature
from pathlib import Path
from typing import Any, TextIO


@dataclass(frozen=True, slots=True)
class CaptureSpec:
    section: str
    title: str
    argv: list[str]
    notes: str = ""
    # catch_exceptions=True in CliRunner for specs that make live network calls
    safe: bool = True


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


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
                "Run from the netbox-cli git checkout or pass --output and --raw-dir."
            )
        return output, raw_dir
    if output is None:
        output = default_out
    if raw_dir is None:
        raw_dir = output.parent / "raw"
    return output, raw_dir


def _inject_stub_config() -> None:
    """Pre-populate cli._RUNTIME_CONFIG so _ensure_runtime_config() returns early."""
    from netbox_cli import cli as cli_mod
    from netbox_cli.config import Config, normalize_base_url

    base_url = os.environ.get("NETBOX_URL", "https://demo.netbox.dev").strip()
    token_key = os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip()
    token_secret = os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip()
    timeout = float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"))
    cli_mod._RUNTIME_CONFIG = Config(
        base_url=normalize_base_url(base_url),
        token_key=token_key,
        token_secret=token_secret,
        timeout=timeout,
    )


def _clear_stub_config() -> None:
    from netbox_cli import cli as cli_mod

    cli_mod._RUNTIME_CONFIG = None


def _truncate(text: str, max_lines: int, max_chars: int) -> tuple[str, bool]:
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n… (truncated by character limit)\n"
        return text, True
    lines = text.splitlines()
    if len(lines) > max_lines:
        head = "\n".join(lines[:max_lines])
        return head + f"\n\n… ({len(lines) - max_lines} more lines truncated)\n", True
    return text, False


def _make_cli_runner() -> Any:
    from typer.testing import CliRunner

    if "mix_stderr" in signature(CliRunner).parameters:
        return CliRunner(mix_stderr=False)
    return CliRunner()


def _run_capture(spec: CaptureSpec, app: Any) -> tuple[int, str, float]:
    _inject_stub_config()
    try:
        runner = _make_cli_runner()
        started = time.perf_counter()
        result = runner.invoke(
            app,
            spec.argv,
            catch_exceptions=not spec.safe,
            color=False,
        )
        elapsed = time.perf_counter() - started
        out = result.stdout or ""
        err = getattr(result, "stderr", "") or ""
        if err.strip():
            out = f"{out}\n--- stderr ---\n{err}" if out.strip() else f"--- stderr ---\n{err}"
        # If an exception was captured (catch_exceptions=True path), surface it
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            import traceback

            tb = "".join(
                traceback.format_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )
            )
            out = f"{out}\n--- exception ---\n{tb}" if out.strip() else f"--- exception ---\n{tb}"
        return result.exit_code or 0, out, elapsed
    finally:
        _clear_stub_config()


def _all_specs() -> list[CaptureSpec]:
    return [
        # ── Top-level help banners (no network, safe) ─────────────────────────
        CaptureSpec("Top-level", "nbx --help", ["--help"]),
        CaptureSpec("Top-level", "nbx init --help", ["init", "--help"]),
        CaptureSpec("Top-level", "nbx config --help", ["config", "--help"]),
        CaptureSpec(
            "Top-level",
            "nbx config",
            ["config"],
            notes="Displays current connection config. Token fields show 'set'/'unset' unless --show-token is passed.",
        ),
        CaptureSpec("Top-level", "nbx groups --help", ["groups", "--help"]),
        CaptureSpec("Top-level", "nbx resources --help", ["resources", "--help"]),
        CaptureSpec("Top-level", "nbx ops --help", ["ops", "--help"]),
        CaptureSpec("Top-level", "nbx call --help", ["call", "--help"]),
        CaptureSpec(
            "Top-level",
            "nbx tui --help",
            ["tui", "--help"],
            notes="Launches the full Textual TUI when invoked without flags. --help shown here only.",
        ),
        CaptureSpec(
            "Top-level",
            "nbx tui --theme",
            ["tui", "--theme"],
            notes="Lists available themes without launching the TUI.",
        ),
        CaptureSpec("Top-level", "nbx docs --help", ["docs", "--help"]),
        CaptureSpec(
            "Top-level",
            "nbx docs generate-capture --help",
            ["docs", "generate-capture", "--help"],
        ),
        # ── Schema discovery (reads reference/openapi/netbox-openapi.json, no network) ──
        CaptureSpec(
            "Schema Discovery",
            "nbx groups",
            ["groups"],
            notes="Lists all OpenAPI app groups from the bundled schema. No network call.",
        ),
        CaptureSpec(
            "Schema Discovery",
            "nbx resources dcim",
            ["resources", "dcim"],
            notes="Lists all resources under the 'dcim' app group.",
        ),
        CaptureSpec(
            "Schema Discovery",
            "nbx ops dcim devices",
            ["ops", "dcim", "devices"],
            notes="Lists HTTP operations (method, path, operationId) for dcim/devices.",
        ),
        CaptureSpec(
            "Schema Discovery",
            "nbx resources ipam",
            ["resources", "ipam"],
            notes="Lists all resources under the 'ipam' app group.",
        ),
        # ── Dynamic sub-commands (registered from OpenAPI schema, no network) ──
        CaptureSpec(
            "Dynamic Commands",
            "nbx dcim --help",
            ["dcim", "--help"],
            notes="Auto-generated Typer sub-app for the 'dcim' OpenAPI group.",
        ),
        CaptureSpec(
            "Dynamic Commands",
            "nbx dcim devices --help",
            ["dcim", "devices", "--help"],
            notes="Auto-generated Typer sub-app for dcim/devices.",
        ),
        CaptureSpec(
            "Dynamic Commands",
            "nbx dcim devices list --help",
            ["dcim", "devices", "list", "--help"],
            notes="Auto-generated list action for dcim/devices.",
        ),
        CaptureSpec(
            "Dynamic Commands",
            "nbx ipam prefixes --help",
            ["ipam", "prefixes", "--help"],
        ),
        # ── Live API calls (require a real NetBox at NETBOX_URL) ──────────────
        CaptureSpec(
            "Live API",
            "nbx call GET /api/status/",
            ["call", "GET", "/api/status/"],
            notes=(
                "Requires a reachable NetBox at NETBOX_URL. "
                "Connection errors are expected in offline runs and are valid documentation."
            ),
            safe=False,
        ),
        CaptureSpec(
            "Live API",
            "nbx call GET /api/dcim/sites/ --json",
            ["call", "GET", "/api/dcim/sites/", "--json"],
            notes="Returns paginated list as raw JSON. Requires a NetBox with a valid token.",
            safe=False,
        ),
        # ── Dynamic form invocation ────────────────────────────────────────────
        CaptureSpec(
            "Dynamic Form",
            "nbx dcim devices list (dynamic form)",
            ["dcim", "devices", "list"],
            notes=(
                "Invoked via the auto-registered Typer sub-command (not dynamic ctx.args path). "
                "Requires live NetBox. Connection errors are expected in offline runs."
            ),
            safe=False,
        ),
    ]


def generate_command_capture_docs(
    *,
    output: Path,
    raw_dir: Path,
    max_lines: int = 200,
    max_chars: int = 120_000,
    log: TextIO | None = None,
) -> int:
    """Write capture Markdown and raw JSON artifacts. Returns 0 on success."""
    log = log or sys.stderr
    from netbox_cli.cli import app as cli_app

    output.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "netbox_url": os.environ.get("NETBOX_URL", "https://demo.netbox.dev"),
        "timeout": os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"),
        "token_key_set": bool(os.environ.get("NETBOX_TOKEN_KEY", "").strip()),
    }

    lines: list[str] = [
        "# NetBox CLI — captured command input and output",
        "",
        "This file is **machine-generated**. Regenerate with:",
        "",
        "```bash",
        "cd /path/to/netbox-cli",
        "pip install -e .   # once",
        "nbx docs generate-capture",
        "# or: python docs/generate_command_docs.py",
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
        f"- **Effective `NETBOX_URL`:** `{meta['netbox_url']}`",
        f"- **Effective timeout (s):** `{meta['timeout']}`",
        f"- **`NETBOX_TOKEN_KEY` set:** `{meta['token_key_set']}`",
        "",
        (
            "> Live API calls (`call`, dynamic-form list/get/…) reflect whatever is reachable "
            "at NETBOX_URL. Connection errors and 401/403 responses are still useful documentation "
            "of real CLI behavior."
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

    section_last = ""
    artifacts: list[dict] = []

    for spec in _all_specs():
        if spec.section != section_last:
            lines.append(f"## {spec.section}")
            lines.append("")
            section_last = spec.section

        cmd_display = "nbx " + " ".join(spec.argv)
        code, out, elapsed = _run_capture(spec, cli_app)

        truncated, did_trunc = _truncate(out, max_lines, max_chars)
        slug = f"{spec.section}-{spec.title}"[:80].lower().replace(" ", "-").replace("/", "-")
        slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug)
        while "--" in slug:
            slug = slug.replace("--", "-")

        art = {
            "section": spec.section,
            "title": spec.title,
            "argv": spec.argv,
            "exit_code": code,
            "elapsed_seconds": round(elapsed, 3),
            "truncated": did_trunc,
        }
        artifacts.append(art)
        (raw_dir / f"{len(artifacts):03d}-{slug}.json").write_text(
            json.dumps({**art, "stdout_full": out}, indent=2),
            encoding="utf-8",
        )

        lines.append(f"### {spec.title}")
        lines.append("")
        lines.append("**Input:**")
        lines.append("")
        lines.append("```bash")
        lines.append(cmd_display)
        lines.append("```")
        lines.append("")
        if spec.notes:
            lines.append(f"*{spec.notes}*")
            lines.append("")
        lines.append(f"**Exit code:** `{code}`  ·  **Wall time (s):** `{elapsed:.3f}`")
        if did_trunc:
            lines.append("")
            lines.append(
                f"*Output truncated for this doc (max {max_lines} lines / {max_chars} chars).*"
            )
        lines.append("")
        lines.append("**Output:**")
        lines.append("")
        lines.append("```text")
        lines.append(truncated.rstrip() or "(empty)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    output.write_text("\n".join(lines), encoding="utf-8")
    (raw_dir / "index.json").write_text(
        json.dumps({"meta": meta, "runs": artifacts}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output}", file=log)
    print(f"Wrote {len(artifacts)} raw JSON files under {raw_dir}", file=log)
    return 0
