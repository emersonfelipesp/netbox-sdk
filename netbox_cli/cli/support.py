"""Shared CLI helpers for errors, tables, tracing output, and theme selection."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

import click
import typer
import yaml
from rich.console import Console
from rich.table import Table

from ..api import NetBoxApiClient
from ..output_safety import safe_text, sanitize_terminal_text
from ..schema import SchemaIndex
from ..theme_registry import ThemeCatalogError
from ..trace_ascii import render_any_trace_ascii
from ..ui.formatting import (
    humanize_field,
    humanize_value,
    key_value_rows,
    order_field_names,
)

console = Console()

_LIST_COLUMNS = {
    "id",
    "name",
    "display",
    "status",
    "type",
    "role",
    "site",
    "location",
    "device",
    "interface",
    "ip",
    "address",
    "prefix",
    "vlan",
    "tenant",
}


def emit_cli_error(message: str, *, exit_code: int = 1) -> int:
    console.print(
        f"[red]Error:[/red] {sanitize_terminal_text(message).strip()}",
        highlight=False,
        soft_wrap=True,
    )
    return exit_code


def format_click_exception(error: click.ClickException) -> str:
    message = error.format_message().strip()
    if isinstance(error, click.UsageError):
        return f"{message}\nRun 'nbx --help' to see available commands."
    return message


def playwright_install_message() -> str:
    return (
        "Playwright is not installed. Install it and the Chromium browser first:\n"
        "  uv sync --dev\n"
        "  uv tool run --from playwright playwright install chromium --with-deps"
    )


def available_theme_names_or_error(
    available_theme_names: Callable[[], tuple[str, ...]],
) -> tuple[str, ...]:
    try:
        return available_theme_names()
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc


def resolve_requested_theme(
    ctx: typer.Context,
    *,
    theme: bool,
    available_theme_names: Callable[[], tuple[str, ...]],
    resolve_theme_name: Callable[[str | None], str | None],
    usage: str,
) -> str | None:
    names = available_theme_names_or_error(available_theme_names)
    if not theme:
        return None
    if not ctx.args:
        typer.echo("Available themes:")
        for name in names:
            typer.echo(f"- {name}")
        return None
    if len(ctx.args) > 1:
        raise typer.BadParameter(f"Too many arguments for --theme. Use: {usage}")

    requested = ctx.args[0]
    resolved = resolve_theme_name(requested)
    if not resolved:
        available = ", ".join(names)
        raise typer.BadParameter(f"Unknown theme '{requested}'. Available themes: {available}")
    return resolved


def run_with_spinner(coro: Any) -> Any:
    with console.status("[bold cyan]Fetching…[/bold cyan]", spinner="dots"):
        return asyncio.run(coro)


def render_table(parsed: Any) -> None:
    if isinstance(parsed, dict) and "results" in parsed and isinstance(parsed["results"], list):
        rows_data = [r for r in parsed["results"] if isinstance(r, dict)]
        count = parsed.get("count")
        render_list_table(rows_data, count=count)
    elif isinstance(parsed, dict):
        render_detail_table(parsed)
    elif isinstance(parsed, list):
        rows_data = [r for r in parsed if isinstance(r, dict)]
        if not rows_data and parsed:
            rows_data = [{"value": sanitize_terminal_text(item)} for item in parsed]
        render_list_table(rows_data, count=None)
    else:
        console.print(safe_text(parsed))


def render_list_table(rows_data: list[dict[str, Any]], *, count: int | None) -> None:
    if not rows_data:
        console.print("[dim]No results.[/dim]")
        return

    all_keys: list[str] = []
    for row in rows_data:
        for key in row.keys():
            if key not in all_keys:
                all_keys.append(str(key))

    priority_keys = [k for k in all_keys if k in _LIST_COLUMNS]
    display_keys = order_field_names(priority_keys if priority_keys else all_keys)

    title = f"{count} result(s)" if count is not None else None
    table = Table(title=title, show_header=True, header_style="bold")
    for key in display_keys:
        table.add_column(humanize_field(key), overflow="fold", no_wrap=False)

    for row in rows_data:
        values = [safe_text(humanize_value(row.get(key))) for key in display_keys]
        table.add_row(*values)

    console.print(table)


def render_detail_table(obj: dict[str, Any]) -> None:
    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("Field", style="bold", no_wrap=True)
    table.add_column("Value", overflow="fold")

    for field_label, cell_text in key_value_rows(obj):
        table.add_row(safe_text(field_label, style="bold"), cell_text)

    console.print(table)


def print_response(
    status: int,
    text: str,
    *,
    as_json: bool = False,
    as_yaml: bool = False,
) -> None:
    typer.echo(f"Status: {status}")
    stripped = text.strip()
    if not stripped:
        return
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        typer.echo(sanitize_terminal_text(stripped))
        return

    if as_json:
        typer.echo(json.dumps(parsed, indent=2, sort_keys=True))
        return

    if as_yaml:
        typer.echo(
            yaml.dump(
                parsed, allow_unicode=True, sort_keys=False, default_flow_style=False
            ).rstrip()
        )
        return

    render_table(parsed)


def trace_message(message: str) -> None:
    typer.echo(f"Cable Trace: {sanitize_terminal_text(message)}")


def print_trace_output(
    *,
    group: str,
    resource: str,
    action: str,
    object_id: int | None,
    client: NetBoxApiClient,
    index: SchemaIndex,
) -> None:
    if action != "get":
        raise typer.BadParameter("--trace is only supported for get actions")
    if object_id is None:
        raise typer.BadParameter("--trace requires --id")

    trace_path = index.trace_path(group, resource)
    paths_path = index.paths_path(group, resource)
    trace_endpoint = trace_path or paths_path
    if not trace_endpoint:
        trace_message("Not available for this resource.")
        return

    response = run_with_spinner(
        client.request("GET", trace_endpoint.replace("{id}", str(object_id)))
    )
    if response.status >= 400:
        detail = response.text.strip().lower()
        if "not found" in detail or "no cable" in detail or "no connected" in detail:
            trace_message("No connected cable trace found.")
            return
        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            detail_text = str(parsed.get("detail") or "").strip().lower()
            if (
                "not found" in detail_text
                or "no cable" in detail_text
                or "no connected" in detail_text
            ):
                trace_message("No connected cable trace found.")
                return
        trace_message(f"Unavailable (HTTP {response.status}).")
        return

    try:
        parsed = json.loads(response.text)
    except json.JSONDecodeError:
        trace_message("Unavailable.")
        return

    rendered = render_any_trace_ascii(parsed)
    if not rendered:
        trace_message("No connected cable trace found.")
        return

    typer.echo("Cable Trace:")
    typer.echo(sanitize_terminal_text(rendered))
