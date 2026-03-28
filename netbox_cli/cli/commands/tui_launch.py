"""TUI and on-disk log viewer commands."""

from __future__ import annotations

import typer

from ...logging_runtime import DEFAULT_LOG_TAIL_LIMIT, render_log_entries
from ...theme_registry import ThemeCatalogError
from ..support import available_theme_names_or_error
from ._wiring import get_bound_client, get_bound_index


def register_tui_launch_commands(app: typer.Typer) -> None:
    @app.command("tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
    def tui_command(
        ctx: typer.Context,
        theme: bool = typer.Option(
            False,
            "--theme",
            help=(
                "Theme selector. Use '--theme' to list available themes or "
                "'--theme <name>' to launch with one."
            ),
        ),
    ) -> None:
        """Launch the interactive NetBox terminal UI."""
        from ...tui import available_theme_names, resolve_theme_name, run_tui  # noqa: PLC0415
        from ...ui.logs_app import run_logs_tui  # noqa: PLC0415

        raw_args = list(ctx.args)
        show_logs = False
        if raw_args and raw_args[0] == "logs":
            show_logs = True
            raw_args = raw_args[1:]

        names = available_theme_names_or_error(available_theme_names)
        if theme:
            if not raw_args:
                typer.echo("Available themes:")
                for name in names:
                    typer.echo(f"- {name}")
                return
            if len(raw_args) > 1:
                usage = "nbx tui logs --theme <name>" if show_logs else "nbx tui --theme <name>"
                raise typer.BadParameter(f"Too many arguments for --theme. Use: {usage}")
            selected_theme = resolve_theme_name(raw_args[0])
            if not selected_theme:
                available = ", ".join(names)
                raise typer.BadParameter(
                    f"Unknown theme '{raw_args[0]}'. Available themes: {available}"
                )
        else:
            selected_theme = None

        if show_logs:
            run_logs_tui(theme_name=selected_theme)
            return

        try:
            run_tui(
                client=get_bound_client(),
                index=get_bound_index(),
                theme_name=selected_theme,
                demo_mode=False,
            )
        except ThemeCatalogError as exc:
            raise typer.BadParameter(f"Theme configuration error: {exc}") from exc

    @app.command("logs")
    def logs_command(
        limit: int = typer.Option(
            DEFAULT_LOG_TAIL_LIMIT,
            "--limit",
            "-n",
            min=1,
            help="Number of most recent log entries to display.",
        ),
        include_source: bool = typer.Option(
            False,
            "--source",
            help="Include module/function/line details in output.",
        ),
    ) -> None:
        """Show recent application logs from the shared on-disk log file."""
        from netbox_cli.cli import log_file_path, read_log_entries  # noqa: PLC0415

        entries = read_log_entries(limit=limit)
        typer.echo(f"Log file: {log_file_path()}")
        if not entries:
            typer.echo("No log entries yet.")
            return
        typer.echo(render_log_entries(entries, include_source=include_source))
