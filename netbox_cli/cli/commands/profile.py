"""Profile and connectivity commands: init, config, test."""

from __future__ import annotations

import json
from typing import Any

import typer

from ...config import (
    DEFAULT_PROFILE,
    Config,
    normalize_base_url,
    resolved_token,
    save_config,
)
from ..runtime import _cache_profile
from ..support import run_with_spinner
from ._wiring import get_bound_client


def register_profile_commands(app: typer.Typer) -> None:
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
        from netbox_cli.cli import _ensure_runtime_config  # noqa: PLC0415

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
        from netbox_cli.cli import _ensure_runtime_config  # noqa: PLC0415

        from ...django_models.fetcher import (  # noqa: PLC0415
            available_build_tags,
            fetch_and_build,
        )

        _ensure_runtime_config()
        probe = run_with_spinner(get_bound_client().probe_connection())
        if not probe.ok:
            detail = probe.error or f"HTTP {probe.status}"
            typer.echo(f"Connection failed: {detail}", err=True)
            raise typer.Exit(code=1)

        version_text = probe.version or "unknown"
        typer.echo(f"Connection OK (status={probe.status}, api_version={version_text})")

        if probe.version:
            from ...django_models.fetcher import _match_tag  # noqa: PLC0415

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
