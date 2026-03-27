"""Shared CLI helpers for errors, tables, tracing output, and theme selection."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from enum import StrEnum
from importlib import import_module
from typing import Any

import click
import typer
import yaml
from rich.console import Console
from rich.table import Table

from netbox_cli.markdown_output import render_markdown
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.formatting import (
    humanize_field,
    humanize_value,
    key_value_rows,
    order_field_names,
)
from netbox_sdk.output_safety import safe_text, sanitize_terminal_text
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.trace_ascii import render_any_trace_ascii

console = Console()
TUI_EXTRA_INSTALL_MESSAGE = "TUI support is not installed. Install with: pip install 'netbox-sdk[tui]'"


def select_json_path(data: Any, path: str) -> Any:
    """Extract a value from nested data using dot notation (e.g., 'results.0.name')."""
    if not path:
        return data
    parts = path.split(".")
    current = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, list):
            try:
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            except ValueError:
                return None
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


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


OUTPUT_FORMAT_CONFLICT_MESSAGE = (
    "Options --json, --yaml, and --markdown are mutually exclusive; pick one"
)


class OutputFormat(StrEnum):
    HUMAN = "human"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"


def resolve_output_format(
    *,
    as_json: bool = False,
    as_yaml: bool = False,
    as_markdown: bool = False,
    error_factory: Callable[[str], Exception] | None = None,
) -> OutputFormat:
    selected: list[OutputFormat] = []
    if as_json:
        selected.append(OutputFormat.JSON)
    if as_yaml:
        selected.append(OutputFormat.YAML)
    if as_markdown:
        selected.append(OutputFormat.MARKDOWN)

    if len(selected) > 1:
        if error_factory is not None:
            raise error_factory(OUTPUT_FORMAT_CONFLICT_MESSAGE)
        raise typer.BadParameter(OUTPUT_FORMAT_CONFLICT_MESSAGE)

    return selected[0] if selected else OutputFormat.HUMAN


def emit_cli_error(message: str, *, exit_code: int = 1) -> int:
    console.print(
        f"[bold]Error:[/bold] {sanitize_terminal_text(message).strip()}",
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


def load_tui_callables(module_path: str, *names: str) -> tuple[Any, ...]:
    try:
        module = import_module(module_path)
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing.startswith("textual") or missing.startswith("netbox_tui"):
            raise typer.BadParameter(TUI_EXTRA_INSTALL_MESSAGE) from exc
        raise
    return tuple(getattr(module, name) for name in names)


def rethrow_theme_catalog_error(exc: Exception) -> None:
    if exc.__class__.__name__ == "ThemeCatalogError":
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc
    raise exc


def available_theme_names_or_error(
    available_theme_names: Callable[[], tuple[str, ...]],
) -> tuple[str, ...]:
    try:
        return available_theme_names()
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


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
    with console.status("[bold]Fetching...[/bold]", spinner="dots"):
        return asyncio.run(coro)


def render_table(parsed: Any, columns: list[str] | None = None, max_columns: int = 6) -> None:
    if isinstance(parsed, dict) and "results" in parsed and isinstance(parsed["results"], list):
        rows_data = [r for r in parsed["results"] if isinstance(r, dict)]
        count = parsed.get("count")
        render_list_table(rows_data, count=count, columns=columns, max_columns=max_columns)
    elif isinstance(parsed, dict):
        render_detail_table(parsed)
    elif isinstance(parsed, list):
        rows_data = [r for r in parsed if isinstance(r, dict)]
        if not rows_data and parsed:
            rows_data = [{"value": sanitize_terminal_text(item)} for item in parsed]
        render_list_table(rows_data, count=None, columns=columns, max_columns=max_columns)
    else:
        console.print(safe_text(parsed))


def render_list_table(
    rows_data: list[dict[str, Any]],
    *,
    count: int | None = None,
    columns: list[str] | None = None,
    max_columns: int = 6,
) -> None:
    if not rows_data:
        console.print("[dim]No results.[/dim]")
        return

    all_keys: list[str] = []
    for row in rows_data:
        for key in row.keys():
            if key not in all_keys:
                all_keys.append(str(key))

    if columns:
        display_keys = [k for k in columns if k in all_keys]
        if not display_keys:
            if not all_keys:
                raise typer.BadParameter(
                    "None of the requested columns exist in the response (rows have no keys)."
                )
            sample = ", ".join(all_keys[:12])
            if len(all_keys) > 12:
                sample += ", …"
            raise typer.BadParameter(
                f"None of the requested columns exist in the response. "
                f"Available keys include: {sample}"
            )
    else:
        priority_keys = [k for k in all_keys if k in _LIST_COLUMNS]
        display_keys = order_field_names(priority_keys if priority_keys else all_keys)

    if max_columns and len(display_keys) > max_columns:
        display_keys = display_keys[:max_columns]

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
    as_markdown: bool = False,
    select_path: str | None = None,
    columns: list[str] | None = None,
    max_columns: int = 6,
) -> None:
    output_format = resolve_output_format(
        as_json=as_json,
        as_yaml=as_yaml,
        as_markdown=as_markdown,
    )
    typer.echo(f"Status: {status}")
    stripped = text.strip()
    if not stripped:
        return
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        typer.echo(sanitize_terminal_text(stripped))
        return

    if output_format is OutputFormat.JSON:
        typer.echo(json.dumps(parsed, indent=2, sort_keys=True))
        return

    if output_format is OutputFormat.YAML:
        typer.echo(
            yaml.dump(
                parsed, allow_unicode=True, sort_keys=False, default_flow_style=False
            ).rstrip()
        )
        return

    if output_format is OutputFormat.MARKDOWN:
        typer.echo(render_markdown(parsed))
        return

    if select_path is not None:
        selected = select_json_path(parsed, select_path)
        if selected is not None:
            if isinstance(selected, (dict, list)):
                typer.echo(json.dumps(selected, indent=2, sort_keys=True))
            else:
                typer.echo(safe_text(selected))
        return

    render_table(parsed, columns=columns, max_columns=max_columns)


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


def print_dry_run(
    *,
    method: str,
    path: str,
    body: dict[str, Any] | list[Any] | None,
) -> None:
    """Print a dry-run preview of a write operation."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="[bold]Dry Run Preview[/bold]", show_header=True, header_style="bold")
    table.add_column("Field", style="bold", no_wrap=True)
    table.add_column("Value", overflow="fold")

    table.add_row("Method", method)
    table.add_row("Path", path)
    if body:
        body_str = json.dumps(body, indent=2)
        table.add_row("Body", body_str)
    else:
        table.add_row("Body", "[dim](none)[/dim]")

    console.print(table)
