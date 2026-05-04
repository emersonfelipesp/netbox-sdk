"""Demo command group for the nbx CLI.

Registers ``nbx demo`` and its subcommands (init, config, test, reset, TUI,
OpenAPI command tree, ``demo dev http``, etc.) that target the demo.netbox.dev
hosted NetBox instance with the same surface area as the default profile CLI.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from importlib import import_module
from types import ModuleType
from typing import Any

import typer

from netbox_cli.runtime import (
    _RUNTIME_CONFIGS,
    _cache_profile,
    _dev_http_client_factory_ctx,
    _ensure_demo_runtime_config,
    _get_client_for_config,
    _get_demo_client,
    _get_index,
    _verify_runtime_config,
)
from netbox_cli.support import (
    load_tui_callables,
    playwright_install_message,
    resolve_requested_theme,
    rethrow_theme_catalog_error,
    run_with_spinner,
)
from netbox_sdk.config import (
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    clear_profile_config,
    is_runtime_config_complete,
    load_profile_config,
    resolved_token,
    save_profile_config,
)

demo_app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="NetBox demo.netbox.dev profile and command tree.",
    no_args_is_help=False,
)

demo_dev_app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Developer-focused tools against the demo.netbox.dev profile.",
    no_args_is_help=True,
)


@demo_dev_app.callback()
def _demo_dev_profile(ctx: typer.Context) -> None:
    """Route ``nbx demo dev http`` through the demo profile API client."""
    token = _dev_http_client_factory_ctx.set(_get_demo_client)

    def _reset_factory() -> None:
        _dev_http_client_factory_ctx.reset(token)

    ctx.call_on_close(_reset_factory)


demo_cli_app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="CLI builder tools against the demo.netbox.dev profile.",
    no_args_is_help=True,
)


def _cli_exports() -> ModuleType:
    return import_module("netbox_cli")


_ORIGINAL_LOAD_PROFILE_CONFIG = load_profile_config
_ORIGINAL_SAVE_PROFILE_CONFIG = save_profile_config
_ORIGINAL_VERIFY_RUNTIME_CONFIG = _verify_runtime_config
_ORIGINAL_ENSURE_DEMO_RUNTIME_CONFIG = _ensure_demo_runtime_config
_ORIGINAL_GET_CLIENT_FOR_CONFIG = _get_client_for_config
_ORIGINAL_GET_DEMO_CLIENT = _get_demo_client
_ORIGINAL_GET_INDEX = _get_index


def _resolve_cli_override(
    name: str, current: Callable[..., Any], original: Callable[..., Any]
) -> Callable[..., Any]:
    if current is not original:
        return current
    candidate = getattr(_cli_exports(), name, None)
    if candidate is not None and candidate is not original:
        return candidate
    return current


def _call_cli_override(
    name: str,
    current: Callable[..., Any],
    original: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    return _resolve_cli_override(name, current, original)(*args, **kwargs)


@demo_app.command(
    "graphql", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def demo_graphql_command(
    ctx: typer.Context,
    query: str = typer.Argument(
        ..., help="GraphQL query string, or 'tui' to launch the GraphQL TUI"
    ),
    variables: list[str] = typer.Option(
        None,
        "--variables",
        "-v",
        help="GraphQL variables: one JSON object, or repeat for multiple key=value pairs",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output raw JSON"),
    output_yaml: bool = typer.Option(False, "--yaml", help="Output YAML"),
    theme: bool = typer.Option(
        False,
        "--theme",
        help="For `nbx demo graphql tui`: list available themes or launch with `--theme <name>`.",
    ),
) -> None:
    """Execute a GraphQL query against the demo NetBox API, or launch the GraphQL TUI."""
    if query == "tui":
        available_theme_names, resolve_theme_name, run_graphql_tui = load_tui_callables(
            "netbox_tui.graphql_app",
            "available_theme_names",
            "resolve_theme_name",
            "run_graphql_tui",
        )

        selected_theme = resolve_requested_theme(
            ctx,
            theme=theme,
            available_theme_names=available_theme_names,
            resolve_theme_name=resolve_theme_name,
            usage="nbx demo graphql tui --theme <name>",
        )
        if theme and not ctx.args:
            return
        if variables or output_json or output_yaml:
            raise typer.BadParameter(
                "--variables, --json, and --yaml are only valid for GraphQL query execution."
            )
        try:
            run_graphql_tui(
                client=_call_cli_override(
                    "_get_demo_client",
                    _get_demo_client,
                    _ORIGINAL_GET_DEMO_CLIENT,
                ),
                theme_name=selected_theme,
            )
        except Exception as exc:
            rethrow_theme_catalog_error(exc)
        return

    if theme:
        raise typer.BadParameter("--theme is only supported for `nbx demo graphql tui`.")
    _cli_exports()._run_graphql_cli_query(
        client=_call_cli_override(
            "_get_demo_client",
            _get_demo_client,
            _ORIGINAL_GET_DEMO_CLIENT,
        ),
        query=query,
        variables=variables,
        output_json=output_json,
        output_yaml=output_yaml,
    )


def _demo_payload(cfg: Config, *, show_token: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "profile": DEMO_PROFILE,
        "base_url": DEMO_BASE_URL,
        "timeout": cfg.timeout,
        "token_version": cfg.token_version,
        "demo_username": cfg.demo_username or "unset",
        "demo_password": "set" if cfg.demo_password else "unset",
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
    demo_username: str | None = None,
    demo_password: str | None = None,
) -> Config:
    existing = _call_cli_override(
        "load_profile_config",
        load_profile_config,
        _ORIGINAL_LOAD_PROFILE_CONFIG,
        DEMO_PROFILE,
    )
    if force:
        _confirm_demo_override(existing)
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v2",
        token_key=token_key.strip() or None,
        token_secret=token_secret.strip() or None,
        demo_username=demo_username,
        demo_password=demo_password,
        timeout=timeout,
    )
    if not cfg.token_key or not cfg.token_secret:
        raise typer.BadParameter(
            "Both --token-key and --token-secret are required when configuring the demo profile directly."
        )
    _call_cli_override(
        "_verify_runtime_config",
        _verify_runtime_config,
        _ORIGINAL_VERIFY_RUNTIME_CONFIG,
        cfg,
        context="Demo token",
        profile=DEMO_PROFILE,
    )
    _call_cli_override(
        "save_profile_config",
        save_profile_config,
        _ORIGINAL_SAVE_PROFILE_CONFIG,
        DEMO_PROFILE,
        cfg,
    )
    typer.echo("Demo configuration saved.")
    return _cache_profile(DEMO_PROFILE, cfg)


def _initialize_demo_profile(
    *,
    force: bool,
    headless: bool = True,
    username: str | None = None,
    password: str | None = None,
    token_key: str | None = None,
    token_secret: str | None = None,
) -> Config:
    existing = _call_cli_override(
        "load_profile_config",
        load_profile_config,
        _ORIGINAL_LOAD_PROFILE_CONFIG,
        DEMO_PROFILE,
    )
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
            demo_username=existing.demo_username,
            demo_password=existing.demo_password,
        )

    if force:
        _confirm_demo_override(existing)

    try:
        from netbox_sdk.demo_auth import bootstrap_demo_profile  # noqa: PLC0415
    except ModuleNotFoundError as exc:
        typer.echo(playwright_install_message(), err=True)
        raise typer.Exit(code=1) from exc

    try:
        import playwright  # noqa: F401
    except ModuleNotFoundError as exc:
        typer.echo(playwright_install_message(), err=True)
        raise typer.Exit(code=1) from exc

    if username is None:
        username = typer.prompt("NetBox demo username")
    if password is None:
        password = typer.prompt("NetBox demo password", hide_input=True)
    try:
        cfg = bootstrap_demo_profile(
            username=username,
            password=password,
            timeout=existing.timeout,
            headless=headless,
        )
        cfg.demo_username = username
        cfg.demo_password = password
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    try:
        _call_cli_override(
            "_verify_runtime_config",
            _verify_runtime_config,
            _ORIGINAL_VERIFY_RUNTIME_CONFIG,
            cfg,
            context="Demo token",
            profile=DEMO_PROFILE,
        )
    except typer.BadParameter as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    _call_cli_override(
        "save_profile_config",
        save_profile_config,
        _ORIGINAL_SAVE_PROFILE_CONFIG,
        DEMO_PROFILE,
        cfg,
    )
    typer.echo("Demo configuration saved.")
    return _cache_profile(DEMO_PROFILE, cfg)


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
            from netbox_cli.dynamic import _handle_dynamic_invocation  # noqa: PLC0415

            _handle_dynamic_invocation(
                ctx.args,
                client_factory=lambda: _call_cli_override(
                    "_get_client_for_config",
                    _get_client_for_config,
                    _ORIGINAL_GET_CLIENT_FOR_CONFIG,
                    _call_cli_override(
                        "_ensure_demo_runtime_config",
                        _ensure_demo_runtime_config,
                        _ORIGINAL_ENSURE_DEMO_RUNTIME_CONFIG,
                    ),
                ),
                index_factory=lambda: _call_cli_override(
                    "_get_index",
                    _get_index,
                    _ORIGINAL_GET_INDEX,
                ),
            )
            return
        if token_key is not None or token_secret is not None:
            _call_cli_override(
                "_initialize_demo_profile",
                _initialize_demo_profile,
                _initialize_demo_profile,
                force=True,
                token_key=token_key,
                token_secret=token_secret,
            )
            return
        cfg = _call_cli_override(
            "load_profile_config",
            load_profile_config,
            _ORIGINAL_LOAD_PROFILE_CONFIG,
            DEMO_PROFILE,
        )
        if not is_runtime_config_complete(cfg):
            _call_cli_override(
                "_initialize_demo_profile",
                _initialize_demo_profile,
                _initialize_demo_profile,
                force=True,
            )
            return
        typer.echo(json.dumps(_demo_payload(cfg, show_token=False), indent=2))


@demo_app.command("init")
def demo_init_command(
    headless: bool = typer.Option(
        True,
        "--headless/--headed",
        help="Run Playwright headless (default). Use --headed only when a desktop/X server is available.",
    ),
    username: str | None = typer.Option(
        None,
        "--username",
        "-u",
        help="demo.netbox.dev username. Prompted interactively when omitted.",
    ),
    password: str | None = typer.Option(
        None,
        "--password",
        "-p",
        help="demo.netbox.dev password. Prompted interactively when omitted.",
    ),
    token_key: str | None = typer.Option(
        None,
        "--token-key",
        help="Set the demo profile directly without Playwright (requires --token-secret).",
    ),
    token_secret: str | None = typer.Option(
        None,
        "--token-secret",
        help="Set the demo profile directly without Playwright (requires --token-key).",
    ),
) -> None:
    """Authenticate with demo.netbox.dev via Playwright and save the demo profile.

    Pass ``--username`` and ``--password`` for non-interactive / CI use.
    Alternatively, supply an existing token directly with ``--token-key`` and
    ``--token-secret`` to skip Playwright entirely.
    """
    _initialize_demo_profile(
        force=True,
        headless=headless,
        username=username,
        password=password,
        token_key=token_key,
        token_secret=token_secret,
    )


@demo_app.command("config")
def demo_config_command(
    show_token: bool = typer.Option(False, "--show-token", help="Include API token in output"),
) -> None:
    """Show the configured demo profile settings."""
    cfg = _call_cli_override(
        "load_profile_config",
        load_profile_config,
        _ORIGINAL_LOAD_PROFILE_CONFIG,
        DEMO_PROFILE,
    )
    typer.echo(json.dumps(_demo_payload(cfg, show_token=show_token), indent=2))


@demo_app.command("test")
def demo_test_command() -> None:
    """Test connectivity to demo.netbox.dev using the configured demo profile."""
    cfg = _call_cli_override(
        "_ensure_demo_runtime_config",
        _ensure_demo_runtime_config,
        _ORIGINAL_ENSURE_DEMO_RUNTIME_CONFIG,
    )
    client = _call_cli_override(
        "_get_client_for_config",
        _get_client_for_config,
        _ORIGINAL_GET_CLIENT_FOR_CONFIG,
        cfg,
    )
    probe = run_with_spinner(
        client.probe_connection(),
        close=client,
    )
    if probe.ok:
        version_text = probe.version or "unknown"
        typer.echo(f"Demo connection OK (status={probe.status}, api_version={version_text})")
        return

    detail = probe.error or f"HTTP {probe.status}"
    typer.echo(f"Demo connection failed: {detail}", err=True)
    raise typer.Exit(code=1)


@demo_app.command("reset")
def demo_reset_command() -> None:
    """Remove the saved demo profile configuration."""
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
    """Launch the TUI against the demo profile."""
    available_theme_names, resolve_theme_name, run_tui = load_tui_callables(
        "netbox_tui",
        "available_theme_names",
        "resolve_theme_name",
        "run_tui",
    )

    selected_theme = resolve_requested_theme(
        ctx,
        theme=theme,
        available_theme_names=available_theme_names,
        resolve_theme_name=resolve_theme_name,
        usage="nbx demo tui --theme <name>",
    )
    if theme and not ctx.args:
        return

    try:
        run_tui(
            client=_call_cli_override(
                "_get_demo_client",
                _get_demo_client,
                _ORIGINAL_GET_DEMO_CLIENT,
            ),
            index=_call_cli_override("_get_index", _get_index, _ORIGINAL_GET_INDEX),
            theme_name=selected_theme,
            demo_mode=True,
        )
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


@demo_dev_app.command(
    "tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def demo_dev_tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    """Launch the developer request workbench TUI against the demo profile."""
    available_theme_names, resolve_theme_name, run_dev_tui = load_tui_callables(
        "netbox_tui.dev_app",
        "available_theme_names",
        "resolve_theme_name",
        "run_dev_tui",
    )

    selected_theme = resolve_requested_theme(
        ctx,
        theme=theme,
        available_theme_names=available_theme_names,
        resolve_theme_name=resolve_theme_name,
        usage="nbx demo dev tui --theme <name>",
    )
    if theme and not ctx.args:
        return

    try:
        run_dev_tui(
            client=_call_cli_override(
                "_get_demo_client",
                _get_demo_client,
                _ORIGINAL_GET_DEMO_CLIENT,
            ),
            index=_call_cli_override("_get_index", _get_index, _ORIGINAL_GET_INDEX),
            theme_name=selected_theme,
        )
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


@demo_cli_app.command(
    "tui", context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def demo_cli_tui_command(
    ctx: typer.Context,
    theme: bool = typer.Option(
        False,
        "--theme",
        help="Theme selector. Use '--theme' to list available themes or '--theme <name>' to launch with one.",
    ),
) -> None:
    """Launch the interactive CLI command builder against the demo profile."""
    available_theme_names, resolve_theme_name, run_cli_tui = load_tui_callables(
        "netbox_tui.cli_tui",
        "available_theme_names",
        "resolve_theme_name",
        "run_cli_tui",
    )

    selected_theme = resolve_requested_theme(
        ctx,
        theme=theme,
        available_theme_names=available_theme_names,
        resolve_theme_name=resolve_theme_name,
        usage="nbx demo cli tui --theme <name>",
    )
    if theme and not ctx.args:
        return

    try:
        run_cli_tui(
            client=_call_cli_override(
                "_get_demo_client",
                _get_demo_client,
                _ORIGINAL_GET_DEMO_CLIENT,
            ),
            index=_call_cli_override("_get_index", _get_index, _ORIGINAL_GET_INDEX),
            theme_name=selected_theme,
            demo_mode=True,
        )
    except Exception as exc:
        rethrow_theme_catalog_error(exc)


demo_app.add_typer(demo_cli_app, name="cli")
demo_app.add_typer(demo_dev_app, name="dev")


def _register_demo_dev_http() -> None:
    from netbox_cli.dev import dev_http_app  # noqa: PLC0415

    demo_dev_app.add_typer(dev_http_app, name="http")


def _register_demo_dev_django_model() -> None:
    from netbox_cli.django_model import django_model_app as _django_model_app  # noqa: PLC0415

    demo_dev_app.add_typer(_django_model_app, name="django-model")
    demo_dev_app.add_typer(_django_model_app, name="django-models")


_register_demo_dev_http()
_register_demo_dev_django_model()
