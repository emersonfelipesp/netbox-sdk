from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .api import NetBoxApiClient
from .config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    clear_profile_config,
    is_runtime_config_complete,
    load_config,
    load_profile_config,
    normalize_base_url,
    resolved_token,
    save_config,
    save_profile_config,
)
from .schema import SchemaIndex, build_schema_index
from .services import load_json_payload, parse_key_value_pairs, run_dynamic_command
from .theme_registry import ThemeCatalogError
from .ui.formatting import (
    _FIELD_PRIORITY,
    humanize_field,
    humanize_value,
    key_value_rows,
    order_field_names,
)

console = Console()
_SCHEMA_INDEX: SchemaIndex | None = None
_RUNTIME_CONFIGS: dict[str, Config] = {}

app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="NetBox API-first CLI/TUI. Dynamic command form: nbx <group> <resource> <action>",
    no_args_is_help=True,
)


def _get_index() -> SchemaIndex:
    global _SCHEMA_INDEX
    if _SCHEMA_INDEX is None:
        _SCHEMA_INDEX = build_schema_index()
    return _SCHEMA_INDEX


def _get_client() -> NetBoxApiClient:
    return NetBoxApiClient(_ensure_runtime_config())


def _get_client_for_config(cfg: Config) -> NetBoxApiClient:
    return NetBoxApiClient(cfg)


def _get_demo_client() -> NetBoxApiClient:
    return _get_client_for_config(_ensure_demo_runtime_config())


@app.callback(invoke_without_command=True)
def root_callback(ctx: typer.Context) -> None:
    if ctx.resilient_parsing:
        return
    if ctx.invoked_subcommand not in {"init", "tui", "docs", "demo"}:
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
    show_token: bool = typer.Option(
        False, "--show-token", help="Include API token in output"
    ),
) -> None:
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


demo_app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="NetBox demo.netbox.dev profile and command tree.",
    no_args_is_help=False,
)


def _demo_payload(cfg: Config, *, show_token: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "profile": DEMO_PROFILE,
        "base_url": DEMO_BASE_URL,
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
    return payload


def _validate_demo_profile(cfg: Config) -> Config:
    if (
        cfg.base_url == DEMO_BASE_URL
        and cfg.token_version == "v2"
        and cfg.token_key
        and cfg.token_secret
    ):
        raise typer.BadParameter(
            "Stored demo profile uses a legacy v2 token configuration. "
            "demo.netbox.dev currently requires v1 tokens for `nbx demo`. "
            "Run `nbx demo init` again, or `nbx demo reset` and reconfigure."
        )
    return cfg


def _confirm_demo_override(existing: Config) -> None:
    if not is_runtime_config_complete(existing):
        return
    should_override = typer.confirm(
        "A demo token is already configured. Override the existing demo config?",
        default=False,
    )
    if not should_override:
        raise typer.Exit(code=1)


def _save_demo_profile_from_token(
    *,
    token_key: str,
    token_secret: str,
    timeout: float,
    force: bool,
) -> Config:
    existing = load_profile_config(DEMO_PROFILE)
    if force:
        _confirm_demo_override(existing)
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v2",
        token_key=token_key.strip() or None,
        token_secret=token_secret.strip() or None,
        timeout=timeout,
    )
    if not cfg.token_key or not cfg.token_secret:
        raise typer.BadParameter(
            "Both --token-key and --token-secret are required when configuring the demo profile directly."
        )
    save_profile_config(DEMO_PROFILE, cfg)
    typer.echo("Demo configuration saved.")
    return _cache_profile(DEMO_PROFILE, cfg)


def _initialize_demo_profile(
    *,
    force: bool,
    headless: bool = True,
    token_key: str | None = None,
    token_secret: str | None = None,
) -> Config:
    existing = load_profile_config(DEMO_PROFILE)
    if not force and is_runtime_config_complete(existing):
        return _cache_profile(DEMO_PROFILE, existing)

    if (token_key is None) ^ (token_secret is None):
        raise typer.BadParameter("Use both --token-key and --token-secret together.")
    if token_key is not None and token_secret is not None:
        return _save_demo_profile_from_token(
            token_key=token_key,
            token_secret=token_secret,
            timeout=existing.timeout,
            force=force,
        )

    if force:
        _confirm_demo_override(existing)

    try:
        from .demo_auth import bootstrap_demo_profile
    except ModuleNotFoundError as exc:
        typer.echo(
            "Playwright is not installed. Install it and the Chromium browser first:\n"
            "  pip install playwright\n"
            "  playwright install chromium",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    try:
        import playwright  # noqa: F401
    except ModuleNotFoundError as exc:
        typer.echo(
            "Playwright is not installed. Install it and the Chromium browser first:\n"
            "  pip install playwright\n"
            "  playwright install chromium",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    username = typer.prompt("NetBox demo username")
    password = typer.prompt("NetBox demo password", hide_input=True)
    try:
        cfg = bootstrap_demo_profile(
            username=username,
            password=password,
            timeout=existing.timeout,
            headless=headless,
        )
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    save_profile_config(DEMO_PROFILE, cfg)
    typer.echo("Demo configuration saved.")
    return _cache_profile(DEMO_PROFILE, cfg)


def _ensure_demo_runtime_config() -> Config:
    return _validate_demo_profile(_ensure_profile_config(DEMO_PROFILE))


@demo_app.callback(invoke_without_command=True)
def demo_callback(
    ctx: typer.Context,
    token_key: str | None = typer.Option(
        None,
        "--token-key",
        help="Set the demo profile directly without Playwright.",
    ),
    token_secret: str | None = typer.Option(
        None,
        "--token-secret",
        help="Set the demo profile directly without Playwright.",
    ),
) -> None:
    if ctx.resilient_parsing:
        return
    if ctx.invoked_subcommand is None:
        if ctx.args:
            _handle_dynamic_invocation(ctx.args, client_factory=_get_demo_client)
            return
        if token_key is not None or token_secret is not None:
            _initialize_demo_profile(
                force=True,
                token_key=token_key,
                token_secret=token_secret,
            )
            return
        cfg = _validate_demo_profile(load_profile_config(DEMO_PROFILE))
        if not is_runtime_config_complete(cfg):
            _initialize_demo_profile(force=True)
            return
        typer.echo(json.dumps(_demo_payload(cfg, show_token=False), indent=2))


@demo_app.command("init")
def demo_init_command(
    headless: bool = typer.Option(
        True,
        "--headless/--headed",
        help="Run Playwright headless by default. Use --headed only when a desktop/X server is available.",
    ),
    token_key: str | None = typer.Option(
        None,
        "--token-key",
        help="Set the demo profile directly without Playwright.",
    ),
    token_secret: str | None = typer.Option(
        None,
        "--token-secret",
        help="Set the demo profile directly without Playwright.",
    ),
) -> None:
    _initialize_demo_profile(
        force=True,
        headless=headless,
        token_key=token_key,
        token_secret=token_secret,
    )


@demo_app.command("config")
def demo_config_command(
    show_token: bool = typer.Option(
        False, "--show-token", help="Include API token in output"
    ),
) -> None:
    cfg = _validate_demo_profile(load_profile_config(DEMO_PROFILE))
    typer.echo(json.dumps(_demo_payload(cfg, show_token=show_token), indent=2))


@demo_app.command("reset")
def demo_reset_command() -> None:
    clear_profile_config(DEMO_PROFILE)
    _RUNTIME_CONFIGS.pop(DEMO_PROFILE, None)
    typer.echo("Demo configuration removed.")


@demo_app.command(
    "tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def demo_tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    from .tui import available_theme_names, resolve_theme_name, run_tui

    try:
        names = available_theme_names()
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc

    selected_theme: str | None = None
    if theme:
        if not ctx.args:
            typer.echo("Available themes:")
            for name in names:
                typer.echo(f"- {name}")
            return
        if len(ctx.args) > 1:
            raise typer.BadParameter(
                "Too many arguments for --theme. Use: nbx demo tui --theme <name>"
            )
        requested = ctx.args[0]
        resolved = resolve_theme_name(requested)
        if not resolved:
            available = ", ".join(names)
            raise typer.BadParameter(
                f"Unknown theme '{requested}'. Available themes: {available}"
            )
        selected_theme = resolved

    try:
        run_tui(
            client=_get_demo_client(), index=_get_index(), theme_name=selected_theme
        )
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc


@app.command("groups")
def groups_command() -> None:
    index = _get_index()
    for group in index.groups():
        typer.echo(group)


@app.command("resources")
def resources_command(
    group: str = typer.Argument(..., help="OpenAPI app group, e.g. dcim"),
) -> None:
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


@app.command("call")
def call_command(
    method: str = typer.Argument(...),
    path: str = typer.Argument(...),
    query: list[str] = typer.Option(
        None, "-q", "--query", help="Query parameter key=value"
    ),
    body_json: str | None = typer.Option(
        None, "--body-json", help="Inline JSON request body"
    ),
    body_file: str | None = typer.Option(
        None, "--body-file", help="Path to JSON request body file"
    ),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
) -> None:
    query_pairs = query or []
    query_dict = parse_key_value_pairs(query_pairs)
    payload = load_json_payload(body_json, body_file)
    response = _run_with_spinner(
        _get_client().request(method, path, query=query_dict, payload=payload)
    )
    _print_response(
        response.status, response.text, as_json=output_json, as_yaml=output_yaml
    )


@app.command(
    "tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    from .tui import available_theme_names, resolve_theme_name, run_tui

    try:
        names = available_theme_names()
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc

    selected_theme: str | None = None
    if theme:
        if not ctx.args:
            typer.echo("Available themes:")
            for name in names:
                typer.echo(f"- {name}")
            return
        if len(ctx.args) > 1:
            raise typer.BadParameter(
                "Too many arguments for --theme. Use: nbx tui --theme <name>"
            )

        requested = ctx.args[0]
        resolved = resolve_theme_name(requested)
        if not resolved:
            available = ", ".join(names)
            raise typer.BadParameter(
                f"Unknown theme '{requested}'. Available themes: {available}"
            )
        selected_theme = resolved

    try:
        run_tui(client=_get_client(), index=_get_index(), theme_name=selected_theme)
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc


def _handle_dynamic_invocation(
    raw_args: list[str],
    *,
    client_factory: Callable[[], NetBoxApiClient] = _get_client,
    index_factory: Callable[[], SchemaIndex] = _get_index,
) -> None:
    if len(raw_args) < 3:
        raise typer.BadParameter(
            "Dynamic invocation requires: nbx <group> <resource> <action> [options]"
        )

    group, resource, action = raw_args[0], raw_args[1], raw_args[2]
    option_args = raw_args[3:]

    object_id, query_pairs, body_json, body_file, as_json, as_yaml = (
        _parse_dynamic_options(option_args)
    )
    response = _execute_dynamic_action(
        group=group,
        resource=resource,
        action=action,
        object_id=object_id,
        query_pairs=query_pairs,
        body_json=body_json,
        body_file=body_file,
        client=client_factory(),
        index=index_factory(),
    )
    _print_response(response.status, response.text, as_json=as_json, as_yaml=as_yaml)


def _parse_dynamic_options(
    args: list[str],
) -> tuple[int | None, list[str], str | None, str | None, bool, bool]:
    object_id: int | None = None
    query_pairs: list[str] = []
    body_json: str | None = None
    body_file: str | None = None
    as_json: bool = False
    as_yaml: bool = False

    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--id"}:
            if i + 1 >= len(args):
                raise typer.BadParameter("--id requires a value")
            object_id = int(args[i + 1])
            i += 2
            continue
        if token in {"-q", "--query"}:
            if i + 1 >= len(args):
                raise typer.BadParameter(f"{token} requires key=value")
            query_pairs.append(args[i + 1])
            i += 2
            continue
        if token == "--body-json":
            if i + 1 >= len(args):
                raise typer.BadParameter("--body-json requires a value")
            body_json = args[i + 1]
            i += 2
            continue
        if token == "--body-file":
            if i + 1 >= len(args):
                raise typer.BadParameter("--body-file requires a path")
            body_file = args[i + 1]
            i += 2
            continue
        if token == "--json":
            as_json = True
            i += 1
            continue
        if token == "--yaml":
            as_yaml = True
            i += 1
            continue
        raise typer.BadParameter(f"Unknown option: {token}")

    return object_id, query_pairs, body_json, body_file, as_json, as_yaml


def _run_with_spinner(coro: Any) -> Any:
    """Run an async coroutine while showing a spinner on stderr."""
    with console.status("[bold cyan]Fetching…[/bold cyan]", spinner="dots"):
        return asyncio.run(coro)


# Compact set for list views — excludes verbose fields (description, url, timestamps)
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


def _render_table(parsed: Any) -> None:
    # Detect paginated list vs single object
    if (
        isinstance(parsed, dict)
        and "results" in parsed
        and isinstance(parsed["results"], list)
    ):
        rows_data = [r for r in parsed["results"] if isinstance(r, dict)]
        count = parsed.get("count")
        _render_list_table(rows_data, count=count)
    elif isinstance(parsed, dict):
        _render_detail_table(parsed)
    elif isinstance(parsed, list):
        rows_data = [r for r in parsed if isinstance(r, dict)]
        if not rows_data and parsed:
            rows_data = [{"value": str(item)} for item in parsed]
        _render_list_table(rows_data, count=None)
    else:
        console.print(str(parsed))


def _render_list_table(rows_data: list[dict[str, Any]], *, count: int | None) -> None:
    if not rows_data:
        console.print("[dim]No results.[/dim]")
        return

    # Collect all keys present in the data, keep only priority ones for compact display
    all_keys: list[str] = []
    for row in rows_data:
        for key in row.keys():
            if key not in all_keys:
                all_keys.append(str(key))

    # Filter to priority columns that actually exist; fall back to all if none match
    priority_keys = [k for k in all_keys if k in _LIST_COLUMNS]
    display_keys = order_field_names(priority_keys if priority_keys else all_keys)

    title = f"{count} result(s)" if count is not None else None
    table = Table(title=title, show_header=True, header_style="bold")
    for key in display_keys:
        table.add_column(humanize_field(key), overflow="fold", no_wrap=False)

    for row in rows_data:
        values = [humanize_value(row.get(key)) for key in display_keys]
        table.add_row(*values)

    console.print(table)


def _render_detail_table(obj: dict[str, Any]) -> None:
    table = Table(show_header=True, header_style="bold", show_lines=True)
    table.add_column("Field", style="bold", no_wrap=True)
    table.add_column("Value", overflow="fold")

    for field_label, cell_text in key_value_rows(obj):
        table.add_row(field_label, str(cell_text))

    console.print(table)


def _print_response(
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
        typer.echo(stripped)
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

    _render_table(parsed)


def _execute_dynamic_action(
    *,
    group: str,
    resource: str,
    action: str,
    object_id: int | None,
    query_pairs: list[str],
    body_json: str | None,
    body_file: str | None,
    client: NetBoxApiClient | None = None,
    index: SchemaIndex | None = None,
):
    return _run_with_spinner(
        run_dynamic_command(
            client=client or _get_client(),
            index=index or _get_index(),
            group=group,
            resource=resource,
            action=action,
            object_id=object_id,
            query_pairs=query_pairs,
            body_json=body_json,
            body_file=body_file,
        )
    )


def _load_cached_profile(profile: str) -> Config | None:
    cfg = _RUNTIME_CONFIGS.get(profile)
    if cfg is not None and is_runtime_config_complete(cfg):
        return cfg
    return None


def _cache_profile(profile: str, cfg: Config) -> Config:
    _RUNTIME_CONFIGS[profile] = cfg
    return cfg


def _ensure_profile_config(profile: str) -> Config:
    cached = _load_cached_profile(profile)
    if cached is not None:
        return cached

    cfg = load_profile_config(profile)
    if is_runtime_config_complete(cfg):
        return _cache_profile(profile, cfg)

    if profile == DEMO_PROFILE:
        return _initialize_demo_profile(force=True)

    typer.echo("NetBox endpoint configuration is required.")
    if not cfg.base_url:
        cfg.base_url = normalize_base_url(
            typer.prompt("NetBox host (example: https://netbox.example.com)")
        )
    if not cfg.token_key:
        cfg.token_key = typer.prompt("NetBox token key")
    if not cfg.token_secret:
        cfg.token_secret = typer.prompt("NetBox token secret", hide_input=True)

    save_config(cfg)
    typer.echo("Configuration saved.")
    return _cache_profile(profile, cfg)


def _ensure_runtime_config() -> Config:
    return _ensure_profile_config(DEFAULT_PROFILE)


def _supported_actions(group: str, resource: str) -> list[str]:
    rows = _get_index().operations_for(group, resource)
    by_pair = {(item.path, item.method.upper()) for item in rows}
    paths = _get_index().resource_paths(group, resource)
    if paths is None:
        return []

    actions: list[str] = []
    if paths.list_path and (paths.list_path, "GET") in by_pair:
        actions.append("list")
    if paths.detail_path and (paths.detail_path, "GET") in by_pair:
        actions.append("get")
    if paths.list_path and (paths.list_path, "POST") in by_pair:
        actions.append("create")
    if paths.detail_path and (paths.detail_path, "PUT") in by_pair:
        actions.append("update")
    if paths.detail_path and (paths.detail_path, "PATCH") in by_pair:
        actions.append("patch")
    if paths.detail_path and (paths.detail_path, "DELETE") in by_pair:
        actions.append("delete")
    return actions


def _build_action_command(
    *,
    group: str,
    resource: str,
    action: str,
    client_factory: Callable[[], NetBoxApiClient] = _get_client,
    index_factory: Callable[[], SchemaIndex] = _get_index,
) -> Callable[..., None]:
    requires_id = action in {"get", "update", "patch", "delete"}
    allows_body = action in {"create", "update", "patch"}

    def _command(
        object_id: int | None = typer.Option(
            None, "--id", help="Object ID for detail operations"
        ),
        query: list[str] | None = typer.Option(
            None, "-q", "--query", help="Query parameter key=value"
        ),
        body_json: str | None = typer.Option(
            None, "--body-json", help="Inline JSON request body"
        ),
        body_file: str | None = typer.Option(
            None, "--body-file", help="Path to JSON request body file"
        ),
        output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
        output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    ) -> None:
        if requires_id and object_id is None:
            raise typer.BadParameter("--id is required for this action")
        if not allows_body and (body_json is not None or body_file is not None):
            raise typer.BadParameter("This action does not accept a request body")

        response = _execute_dynamic_action(
            group=group,
            resource=resource,
            action=action,
            object_id=object_id,
            query_pairs=query or [],
            body_json=body_json,
            body_file=body_file,
            client=client_factory(),
            index=index_factory(),
        )
        _print_response(
            response.status, response.text, as_json=output_json, as_yaml=output_yaml
        )

    return _command


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
    max_lines: int = typer.Option(
        200, "--max-lines", help="Max lines per command output in the Markdown."
    ),
    max_chars: int = typer.Option(
        120_000, "--max-chars", help="Max chars per command output in the Markdown."
    ),
) -> None:
    """Capture every nbx command (input + output) and write docs/generated/nbx-command-capture.md."""
    from .docgen_capture import generate_command_capture_docs, resolve_capture_paths

    try:
        out, raw = resolve_capture_paths(output, raw_dir)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    code = generate_command_capture_docs(
        output=out,
        raw_dir=raw,
        max_lines=max_lines,
        max_chars=max_chars,
    )
    raise typer.Exit(code=code)


app.add_typer(docs_app, name="docs")
app.add_typer(demo_app, name="demo")


def _register_openapi_subcommands(
    target_app: typer.Typer,
    *,
    client_factory: Callable[[], NetBoxApiClient] = _get_client,
    index_factory: Callable[[], SchemaIndex] = _get_index,
) -> None:
    index = _get_index()
    for group in index.groups():
        group_typer = typer.Typer(
            no_args_is_help=True,
            help=f"OpenAPI app group: {group}",
        )
        target_app.add_typer(group_typer, name=group)

        for resource in index.resources(group):
            resource_typer = typer.Typer(
                no_args_is_help=True,
                help=f"Resource: {group}/{resource}",
            )
            group_typer.add_typer(resource_typer, name=resource)

            for action in _supported_actions(group, resource):
                cmd = _build_action_command(
                    group=group,
                    resource=resource,
                    action=action,
                    client_factory=client_factory,
                    index_factory=index_factory,
                )
                resource_typer.command(
                    name=action, help=f"{action} {group}/{resource}"
                )(cmd)


_register_openapi_subcommands(app)
_register_openapi_subcommands(demo_app, client_factory=_get_demo_client)


if __name__ == "__main__":
    app()
