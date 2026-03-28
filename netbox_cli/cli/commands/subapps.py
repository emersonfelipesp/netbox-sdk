"""Nested Typer apps: ``nbx cli``, ``nbx docs``."""

from __future__ import annotations

from pathlib import Path

import typer

from ._wiring import get_bound_client, get_bound_index


def build_cli_builder_app() -> typer.Typer:
    cli_app = typer.Typer(
        no_args_is_help=True,
        help="CLI utilities: interactive command builder and helpers.",
    )

    @cli_app.command("tui")
    def cli_tui_command() -> None:
        """Launch the interactive CLI command builder TUI.

        Presents a navigable menu tree (group → resource → action) that
        progressively builds an ``nbx`` command, then executes it and
        shows the output — all without leaving the terminal.
        """
        from ...ui.cli_tui import run_cli_tui  # noqa: PLC0415

        run_cli_tui(client=get_bound_client(), index=get_bound_index())

    return cli_app


def build_docs_app() -> typer.Typer:
    docs_app = typer.Typer(
        no_args_is_help=True,
        help="Generate reference documentation (captured CLI input/output).",
    )

    @docs_app.command("generate-capture")
    def docs_generate_capture(
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Markdown destination. Default: <repo>/docs/generated/nbx-command-capture.md",
        ),
        raw_dir: Path | None = typer.Option(
            None,
            "--raw-dir",
            help="Raw JSON artifacts directory. Default: <repo>/docs/generated/raw/",
        ),
        live: bool = typer.Option(
            False,
            "--live",
            help=(
                "Use the default profile (your real NetBox) instead of the demo profile. "
                "By default the generator captures live-API specs against demo.netbox.dev."
            ),
        ),
        markdown: bool = typer.Option(
            True,
            "--markdown/--no-markdown",
            help=(
                "Append --markdown to dynamic list/get/… and ``nbx call`` captures so tables "
                "are plain Markdown (not Rich). Default: on."
            ),
        ),
        concurrency: int = typer.Option(
            4,
            "--concurrency",
            "-j",
            min=1,
            max=16,
            help="Max parallel CLI captures. Higher values speed up generation but increase NetBox load.",
        ),
    ) -> None:
        """Capture every nbx command (input + output) and write docs/generated/nbx-command-capture.md.

        By default live-API specs run through ``nbx demo …`` (demo.netbox.dev).
        Pass ``--live`` to run them against your configured default profile instead.
        """
        from ...docgen_capture import (  # noqa: PLC0415
            generate_command_capture_docs,
            resolve_capture_paths,
        )

        try:
            out, raw = resolve_capture_paths(output, raw_dir)
        except FileNotFoundError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(code=1) from exc
        code = generate_command_capture_docs(
            output=out,
            raw_dir=raw,
            use_demo=not live,
            markdown_output=markdown,
            max_concurrency=concurrency,
        )
        raise typer.Exit(code=code)

    return docs_app
