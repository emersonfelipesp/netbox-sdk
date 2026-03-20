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
    # safe=True → catch_exceptions=False (local/schema commands, fail fast on bugs)
    # safe=False → catch_exceptions=True (live API calls, connection errors are valid docs)
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


def _inject_stub_config(profile: str) -> bool:
    """Ensure ``cli._RUNTIME_CONFIGS[profile]`` is populated before CliRunner invocations.

    If a complete config already exists on disk for this profile it is loaded into the
    in-process cache (so commands don't re-read disk on every spec) and ``False`` is
    returned — meaning the caller should *not* clear the cache afterwards.

    If no real config exists, a placeholder stub is injected so that live-API specs
    produce a 401/403 response instead of triggering interactive prompts.  ``True`` is
    returned so the caller knows to clear the injected entry after the invocation.
    """
    from netbox_cli import cli as cli_mod
    from netbox_cli.config import (
        DEMO_BASE_URL,
        Config,
        is_runtime_config_complete,
        load_profile_config,
        normalize_base_url,
    )

    existing = load_profile_config(profile)
    if is_runtime_config_complete(existing):
        cli_mod._RUNTIME_CONFIGS[profile] = existing
        return False  # real config loaded — caller must not clear it

    # No real config — inject a placeholder so live calls fail gracefully.
    if profile == "demo":
        base_url = DEMO_BASE_URL
    else:
        raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
        base_url = normalize_base_url(raw)

    token_key = os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip()
    token_secret = os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip()
    timeout = float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"))
    cli_mod._RUNTIME_CONFIGS[profile] = Config(
        base_url=base_url,
        token_key=token_key,
        token_secret=token_secret,
        timeout=timeout,
    )
    return True  # stub injected — caller must clear it afterwards


def _clear_stub_config(profile: str) -> None:
    from netbox_cli import cli as cli_mod

    cli_mod._RUNTIME_CONFIGS.pop(profile, None)


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


def _run_capture(spec: CaptureSpec, app: Any, *, profile: str) -> tuple[int, str, float]:
    was_stub = _inject_stub_config(profile)
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
            out = (
                f"{out}\n--- stderr ---\n{err}"
                if out.strip()
                else f"--- stderr ---\n{err}"
            )
        # Surface captured exceptions (catch_exceptions=True path) as readable text.
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            import traceback

            tb = "".join(
                traceback.format_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )
            )
            out = (
                f"{out}\n--- exception ---\n{tb}"
                if out.strip()
                else f"--- exception ---\n{tb}"
            )
        return result.exit_code or 0, out, elapsed
    finally:
        if was_stub:
            _clear_stub_config(profile)


def _all_specs(*, use_demo: bool = True) -> list[CaptureSpec]:
    """Return the ordered list of capture specs.

    Args:
        use_demo: When True (default) live-API specs invoke commands through
            ``nbx demo …`` so they hit demo.netbox.dev with the configured demo
            profile.  When False they hit the default profile (real NetBox).
    """
    # ── Shared: help banners and schema-discovery (no network, no profile) ────
    specs: list[CaptureSpec] = [
        # Top-level help banners
        CaptureSpec("Top-level", "nbx --help", ["--help"]),
        CaptureSpec("Top-level", "nbx init --help", ["init", "--help"]),
        CaptureSpec("Top-level", "nbx config --help", ["config", "--help"]),
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
        # Demo sub-app help
        CaptureSpec("Demo profile", "nbx demo --help", ["demo", "--help"]),
        CaptureSpec("Demo profile", "nbx demo init --help", ["demo", "init", "--help"]),
        CaptureSpec(
            "Demo profile", "nbx demo config --help", ["demo", "config", "--help"]
        ),
        # Schema discovery (reads reference/openapi/netbox-openapi.json — no network)
        CaptureSpec(
            "Schema Discovery",
            "nbx groups",
            ["groups"],
            notes="Lists all OpenAPI app groups from the local schema file. No network call.",
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
        ),
        # Dynamic sub-commands: --help is safe (no network)
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
        ),
        CaptureSpec("Dynamic Commands", "nbx ipam prefixes --help", ["ipam", "prefixes", "--help"]),
    ]

    # ── Live API specs: differ between demo and default profile ───────────────
    if use_demo:
        specs += [
            CaptureSpec(
                "Live API — demo.netbox.dev",
                "nbx demo dcim devices list",
                ["demo", "dcim", "devices", "list"],
                notes=(
                    "Runs against demo.netbox.dev using the configured demo profile. "
                    "Returns real data when the demo token is valid; 401/403 otherwise."
                ),
                safe=False,
            ),
            CaptureSpec(
                "Live API — demo.netbox.dev",
                "nbx demo ipam prefixes list",
                ["demo", "ipam", "prefixes", "list"],
                notes="Requires a valid demo profile token.",
                safe=False,
            ),
            CaptureSpec(
                "Live API — demo.netbox.dev",
                "nbx demo dcim sites list",
                ["demo", "dcim", "sites", "list"],
                safe=False,
            ),
        ]
    else:
        specs += [
            CaptureSpec(
                "Live API — default profile",
                "nbx call GET /api/status/",
                ["call", "GET", "/api/status/"],
                notes=(
                    "Requires a reachable NetBox at NETBOX_URL. "
                    "Connection errors are expected in offline runs and are still valid documentation."
                ),
                safe=False,
            ),
            CaptureSpec(
                "Live API — default profile",
                "nbx call GET /api/dcim/sites/ --json",
                ["call", "GET", "/api/dcim/sites/", "--json"],
                notes="Returns paginated list as raw JSON. Requires a configured default profile.",
                safe=False,
            ),
            CaptureSpec(
                "Live API — default profile",
                "nbx dcim devices list",
                ["dcim", "devices", "list"],
                notes="Dynamic sub-command against the default profile NetBox instance.",
                safe=False,
            ),
        ]

    return specs


def generate_command_capture_docs(
    *,
    output: Path,
    raw_dir: Path,
    max_lines: int = 200,
    max_chars: int = 120_000,
    use_demo: bool = True,
    log: TextIO | None = None,
) -> int:
    """Write capture Markdown and raw JSON artifacts. Returns 0 on success."""
    log = log or sys.stderr
    from netbox_cli.cli import app as cli_app
    from netbox_cli.config import DEMO_PROFILE, DEFAULT_PROFILE

    profile = DEMO_PROFILE if use_demo else DEFAULT_PROFILE

    output.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Determine effective base_url for the chosen profile for metadata display.
    from netbox_cli.config import DEMO_BASE_URL, load_profile_config

    cfg = load_profile_config(profile)
    effective_url = cfg.base_url or (
        DEMO_BASE_URL if use_demo else os.environ.get("NETBOX_URL", "https://netbox.example.com")
    )
    token_configured = bool(cfg.token_key and cfg.token_secret)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile,
        "netbox_url": effective_url,
        "timeout": os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"),
        "token_configured": token_configured,
    }

    profile_note = (
        "**demo profile** (`nbx demo …` commands → demo.netbox.dev)"
        if use_demo
        else "**default profile** (`nbx …` commands → your configured NetBox)"
    )

    lines: list[str] = [
        "# NetBox CLI — captured command input and output",
        "",
        "This file is **machine-generated**. Regenerate with:",
        "",
        "```bash",
        "cd /path/to/netbox-cli",
        "pip install -e .   # once",
        "nbx docs generate-capture            # demo profile (default)",
        "nbx docs generate-capture --live     # default profile (real NetBox)",
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
        f"- **Profile used:** {profile_note}",
        f"- **Effective NetBox URL:** `{meta['netbox_url']}`",
        f"- **Effective timeout (s):** `{meta['timeout']}`",
        f"- **Token configured:** `{meta['token_configured']}`",
        "",
        (
            "> Live API calls reflect whatever is reachable at the configured URL. "
            "Connection errors and 401/403 responses are still useful documentation "
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

    for spec in _all_specs(use_demo=use_demo):
        if spec.section != section_last:
            lines.append(f"## {spec.section}")
            lines.append("")
            section_last = spec.section

        cmd_display = "nbx " + " ".join(spec.argv)
        code, out, elapsed = _run_capture(spec, cli_app, profile=profile)

        truncated, did_trunc = _truncate(out, max_lines, max_chars)
        slug = (
            f"{spec.section}-{spec.title}"[:80]
            .lower()
            .replace(" ", "-")
            .replace("/", "-")
        )
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
