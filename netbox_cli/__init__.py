"""Typer CLI entrypoints and command registration for the NetBox CLI application."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import click
    import typer
except ModuleNotFoundError as exc:
    missing = exc.name or ""
    if missing in {"click", "typer"}:
        raise ModuleNotFoundError(
            "netbox_cli requires optional CLI dependencies. Install with: pip install 'netbox-sdk[cli]'"
        ) from exc
    raise
from rich.table import Table

from netbox_cli import demo as demo
from netbox_cli.demo import demo_app
from netbox_cli.dev import dev_app
from netbox_cli.dynamic import _handle_dynamic_invocation, _register_openapi_subcommands
from netbox_cli.runtime import (
    _RUNTIME_CONFIGS as _RUNTIME_CONFIGS,  # re-exported so docgen_capture can access cli._RUNTIME_CONFIGS
)
from netbox_cli.runtime import (
    _cache_profile,
    _ensure_runtime_config,
    _get_client,
    _get_index,
)
from netbox_cli.runtime import (
    _ensure_demo_runtime_config as _ensure_demo_runtime_config,
)
from netbox_cli.runtime import (
    _get_client_for_config as _get_client_for_config,
)
from netbox_cli.runtime import (
    _get_demo_client as _get_demo_client,
)
from netbox_cli.runtime import (
    _verify_runtime_config as _verify_runtime_config,
)
from netbox_cli.support import (
    available_theme_names_or_error,
    console,
    emit_cli_error,
    format_click_exception,
    load_tui_callables,
    print_response,
    resolve_output_format,
    rethrow_theme_catalog_error,
    run_with_spinner,
)
from netbox_sdk.config import (
    DEFAULT_PROFILE,
    Config,
    normalize_base_url,
    resolved_token,
    save_config,
)
from netbox_sdk.config import (
    load_profile_config as load_profile_config,
)
from netbox_sdk.config import (
    save_profile_config as save_profile_config,
)
from netbox_sdk.logging_runtime import (
    DEFAULT_LOG_TAIL_LIMIT,
    log_file_path,
    read_log_entries,
    render_log_entries,
    setup_logging,
)
from netbox_sdk.services import (
    load_json_payload,
    parse_key_value_pairs,
)
from netbox_sdk.services import (
    run_dynamic_command as run_dynamic_command,
)

_initialize_demo_profile = demo._initialize_demo_profile
cli = sys.modules[__name__]

app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="NetBox API-first CLI/TUI. Dynamic command form: nbx <group> <resource> <action>",
    no_args_is_help=True,
)


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    command = typer.main.get_command(app)
    try:
        command.main(
            args=argv,
            prog_name="nbx",
            standalone_mode=False,
        )
    except KeyboardInterrupt:
        return emit_cli_error("Command cancelled.", exit_code=130)
    except click.Abort:
        return emit_cli_error("Command cancelled.", exit_code=130)
    except click.ClickException as exc:
        return emit_cli_error(format_click_exception(exc), exit_code=exc.exit_code)
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        return emit_cli_error(
            f"Unexpected failure: {detail}. Please retry or check your configuration."
        )
    return 0


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
        _ensure_runtime_config()
    if ctx.invoked_subcommand is None and ctx.args:
        _handle_dynamic_invocation(ctx.args)


@app.command("init")
def init_command(
    base_url: str = typer.Option(
        ..., prompt=True, help="NetBox base URL, e.g. https://netbox.example.com"
    ),
    token_key: str = typer.Option(..., prompt=True, help="NetBox API token key"),
    token_secret: str = typer.Option(
        ..., prompt=True, hide_input=True, help="NetBox API token secret"
    ),
    timeout: float = typer.Option(30.0, help="HTTP timeout in seconds"),
) -> None:
    """Create or update the default NetBox CLI profile."""
    cfg = Config(
        base_url=normalize_base_url(base_url),
        token_key=token_key.strip() or None,
        token_secret=token_secret.strip() or None,
        timeout=timeout,
    )
    save_config(cfg)
    _cache_profile(DEFAULT_PROFILE, cfg)
    typer.echo("Configuration saved")


@app.command("config")
def config_command(
    show_token: bool = typer.Option(False, "--show-token", help="Include API token in output"),
) -> None:
    """Show the current default profile configuration."""
    cfg = _ensure_runtime_config()
    payload: dict[str, Any] = {
        "base_url": cfg.base_url,
        "timeout": cfg.timeout,
        "token_version": cfg.token_version,
    }
    if show_token:
        payload["token"] = resolved_token(cfg)
        payload["token_key"] = cfg.token_key
        payload["token_secret"] = cfg.token_secret
    else:
        payload["token"] = "set" if resolved_token(cfg) else "unset"
        payload["token_key"] = "set" if cfg.token_key else "unset"
        payload["token_secret"] = "set" if cfg.token_secret else "unset"
    typer.echo(json.dumps(payload, indent=2))


@app.command("test")
def test_command(
    fetch: bool = typer.Option(
        False,
        "--fetch",
        "-f",
        help="If no matching build exists, fetch the release from GitHub and build it.",
    ),
) -> None:
    """Test connectivity to your configured NetBox instance (default profile).

    Also checks if a Django model graph build exists for the detected version.
    Use --fetch to automatically clone and build from GitHub if missing.
    """
    from netbox_cli.support import run_with_spinner  # noqa: PLC0415
    from netbox_sdk.django_models.fetcher import (  # noqa: PLC0415
        available_build_tags,
        fetch_and_build,
    )

    _ensure_runtime_config()
    probe = run_with_spinner(_get_client().probe_connection())
    if not probe.ok:
        detail = probe.error or f"HTTP {probe.status}"
        typer.echo(f"Connection failed: {detail}", err=True)
        raise typer.Exit(code=1)

    version_text = probe.version or "unknown"
    typer.echo(f"Connection OK (status={probe.status}, api_version={version_text})")

    # ── Check for matching build ──────────────────────────────────────────
    if probe.version:
        from netbox_sdk.django_models.fetcher import _match_tag  # noqa: PLC0415

        tags = available_build_tags()
        matched = _match_tag(probe.version, tags)
        if matched:
            typer.echo(f"Matching build found: {matched}")
        elif fetch:
            typer.echo(f"No build found for NetBox API {probe.version}.")
            fetch_and_build(probe.version, confirm=True)
        else:
            typer.echo(f"No build found for NetBox API {probe.version}.")
            typer.echo("Run with --fetch to clone from GitHub and build it.")


@app.command("groups")
def groups_command() -> None:
    """List all available OpenAPI app groups."""
    index = _get_index()
    for group in index.groups():
        typer.echo(group)


@app.command("resources")
def resources_command(
    group: str = typer.Argument(..., help="OpenAPI app group, e.g. dcim"),
) -> None:
    """List resources available within a group."""
    index = _get_index()
    resources = index.resources(group)
    if not resources:
        raise typer.BadParameter(f"Group not found or has no resources: {group}")
    for resource in resources:
        typer.echo(resource)


@app.command("ops")
def operations_command(
    group: str = typer.Argument(...),
    resource: str = typer.Argument(...),
) -> None:
    """Show available HTTP operations for a resource."""
    index = _get_index()
    rows = index.operations_for(group, resource)
    if not rows:
        raise typer.BadParameter(f"No operations found for {group}/{resource}")

    table = Table(title=f"{group}/{resource}")
    table.add_column("Method", no_wrap=True)
    table.add_column("Path")
    table.add_column("Operation ID")
    for row in rows:
        table.add_row(row.method, row.path, row.operation_id or "-")
    console.print(table)


@app.command("graphql")
def graphql_command(
    query: str = typer.Argument(..., help="GraphQL query string"),
    variables: list[str] = typer.Option(
        None,
        "--variables",
        "-v",
        help="GraphQL variables: one JSON object, or repeat for multiple key=value pairs",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
) -> None:
    """Execute a GraphQL query against the NetBox API."""
    client = _get_client()

    vars_dict: dict[str, Any] | None = None
    pairs = variables or []
    if pairs:
        if len(pairs) == 1:
            raw = pairs[0]
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError:
                try:
                    vars_dict = parse_key_value_pairs(pairs)
                except ValueError as exc:
                    raise typer.BadParameter(str(exc)) from exc
            else:
                if not isinstance(decoded, dict):
                    raise typer.BadParameter("GraphQL variables JSON must decode to an object")
                vars_dict = decoded
        else:
            try:
                vars_dict = parse_key_value_pairs(pairs)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc

    response = run_with_spinner(client.graphql(query, vars_dict))
    print_response(
        response.status,
        response.text,
        as_json=output_json,
        as_yaml=output_yaml,
    )


@app.command("call")
def call_command(
    method: str = typer.Argument(...),
    path: str = typer.Argument(...),
    query: list[str] = typer.Option(None, "-q", "--query", help="Query parameter key=value"),
    body_json: str | None = typer.Option(None, "--body-json", help="Inline JSON request body"),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Path to JSON request body file"
    ),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    output_markdown: bool = typer.Option(
        False,
        "--markdown",
        help="Output Markdown (mutually exclusive with --json/--yaml)",
    ),
) -> None:
    """Call an arbitrary NetBox API path."""
    resolve_output_format(
        as_json=output_json,
        as_yaml=output_yaml,
        as_markdown=output_markdown,
    )
    query_pairs = query or []
    query_dict = parse_key_value_pairs(query_pairs)
    payload = load_json_payload(body_json, body_file)
    response = run_with_spinner(
        _get_client().request(method, path, query=query_dict, payload=payload)
    )
    print_response(
        response.status,
        response.text,
        as_json=output_json,
        as_yaml=output_yaml,
        as_markdown=output_markdown,
    )


@app.command("tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    """Launch the interactive NetBox terminal UI."""
    available_theme_names, resolve_theme_name, run_tui = load_tui_callables(
        "netbox_tui",
        "available_theme_names",
        "resolve_theme_name",
        "run_tui",
    )
    (run_logs_tui,) = load_tui_callables("netbox_tui.logs_app", "run_logs_tui")

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
            client=_get_client(),
            index=_get_index(),
            theme_name=selected_theme,
            demo_mode=False,
        )
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


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
    entries = read_log_entries(limit=limit)
    typer.echo(f"Log file: {log_file_path()}")
    if not entries:
        typer.echo("No log entries yet.")
        return
    typer.echo(render_log_entries(entries, include_source=include_source))


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
    (run_cli_tui,) = load_tui_callables("netbox_tui.cli_tui", "run_cli_tui")

    run_cli_tui(client=_get_client(), index=_get_index())


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
    from docgen_capture import (  # noqa: PLC0415
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


app.add_typer(cli_app, name="cli")
app.add_typer(docs_app, name="docs")
app.add_typer(demo_app, name="demo")
app.add_typer(dev_app, name="dev")

_register_openapi_subcommands(app)
_register_openapi_subcommands(
    demo_app,
    client_factory=lambda: _get_client_for_config(_ensure_demo_runtime_config()),
    index_factory=lambda: _get_index(),
)


if __name__ == "__main__":
    raise SystemExit(main())
