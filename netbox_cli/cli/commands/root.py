"""Root Typer callback (logging, config preload, dynamic argv)."""

from __future__ import annotations

import typer

from ...logging_runtime import setup_logging
from ..dynamic import _handle_dynamic_invocation


def register_root_callback(app: typer.Typer) -> None:
    @app.callback(invoke_without_command=True)
    def root_callback(ctx: typer.Context) -> None:
        setup_logging()
        if ctx.resilient_parsing:
            return
        if ctx.invoked_subcommand not in {
            "init",
            "tui",
            "cli",
            "docs",
            "demo",
            "dev",
            "logs",
            "graphql",
        }:
            from netbox_cli.cli import _ensure_runtime_config  # noqa: PLC0415

            _ensure_runtime_config()
        if ctx.invoked_subcommand is None and ctx.args:
            _handle_dynamic_invocation(ctx.args)
