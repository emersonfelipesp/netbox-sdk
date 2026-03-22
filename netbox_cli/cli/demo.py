"""Demo command group for the nbx CLI.

Registers ``nbx demo`` and its subcommands (init, config, test, reset, tui)
that interact with the demo.netbox.dev hosted NetBox instance.
"""

from __future__ import annotations

import json
from typing import Any

import typer

from ..config import (
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    clear_profile_config,
    is_runtime_config_complete,
    load_profile_config,
    resolved_token,
    save_profile_config,
)
from ..theme_registry import ThemeCatalogError
from .runtime import (
    _RUNTIME_CONFIGS,
    _cache_profile,
    _ensure_demo_runtime_config,
    _get_client_for_config,
    _get_demo_client,
    _get_index,
    _verify_runtime_config,
)
from .support import playwright_install_message, resolve_requested_theme, run_with_spinner

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
    existing = load_profile_config(DEMO_PROFILE)
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
    _verify_runtime_config(cfg, context="Demo token")
    save_profile_config(DEMO_PROFILE, cfg)
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
            demo_username=existing.demo_username,
            demo_password=existing.demo_password,
        )

    if force:
        _confirm_demo_override(existing)

    try:
        from ..demo_auth import bootstrap_demo_profile  # noqa: PLC0415
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
        _verify_runtime_config(cfg, context="Demo token")
    except typer.BadParameter as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    save_profile_config(DEMO_PROFILE, cfg)
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
            from .dynamic import _handle_dynamic_invocation  # noqa: PLC0415

            _handle_dynamic_invocation(ctx.args, client_factory=_get_demo_client)
            return
        if token_key is not None or token_secret is not None:
            _initialize_demo_profile(
                force=True,
                token_key=token_key,
                token_secret=token_secret,
            )
            return
        cfg = load_profile_config(DEMO_PROFILE)
        if not is_runtime_config_complete(cfg):
            _initialize_demo_profile(force=True)
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
    cfg = load_profile_config(DEMO_PROFILE)
    typer.echo(json.dumps(_demo_payload(cfg, show_token=show_token), indent=2))


@demo_app.command("test")
def demo_test_command() -> None:
    """Test connectivity to demo.netbox.dev using the configured demo profile."""
    cfg = _ensure_demo_runtime_config()
    probe = run_with_spinner(_get_client_for_config(cfg).probe_connection())
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
    from ..tui import available_theme_names, resolve_theme_name, run_tui  # noqa: PLC0415

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
            client=_get_demo_client(),
            index=_get_index(),
            theme_name=selected_theme,
            demo_mode=True,
        )
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc


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
    from ..dev_tui import available_theme_names, resolve_theme_name, run_dev_tui  # noqa: PLC0415

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
            client=_get_demo_client(),
            index=_get_index(),
            theme_name=selected_theme,
        )
    except ThemeCatalogError as exc:
        raise typer.BadParameter(f"Theme configuration error: {exc}") from exc


demo_app.add_typer(demo_dev_app, name="dev")
