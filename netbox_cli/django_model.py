"""CLI integration for Django model inspector.

Adds ``nbx dev django-model build`` and ``nbx dev django-model tui``.
"""

from __future__ import annotations

from pathlib import Path

import typer

from netbox_sdk.django_models.store import DjangoModelStore

django_model_app = typer.Typer(
    no_args_is_help=True,
    help="Inspect NetBox Django models: parse, cache, and visualize relationships.",
)

_DEFAULT_NETBOX_ROOT = Path("/root/nms/netbox/netbox/")


@django_model_app.command("build")
def django_model_build(
    netbox_root: Path = typer.Option(
        _DEFAULT_NETBOX_ROOT,
        "--netbox-root",
        "-n",
        help="Path to the NetBox Django project root (contains dcim/, ipam/, etc.).",
    ),
    rebuild: bool = typer.Option(
        False,
        "--rebuild",
        "-r",
        help="Force rebuild even if cache exists.",
    ),
    cache_path: Path | None = typer.Option(
        None,
        "--cache-path",
        "-o",
        help="Output path for the JSON build file (default: ~/.config/netbox-sdk/django_models.json).",
    ),
) -> None:
    """Parse NetBox Django models and build the static cache.

    Run this once (or when NetBox is updated) to generate the model graph
    used by the TUI.
    """
    store = DjangoModelStore(cache_path=cache_path)
    if store.exists() and not rebuild:
        typer.echo(f"Cache already exists at {store.path}. Use --rebuild to refresh.")
        raise typer.Exit(code=0)

    if not netbox_root.is_dir():
        typer.echo(f"Error: NetBox source not found at {netbox_root}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Scanning {netbox_root}...")
    graph = store.build(netbox_root)
    stats = graph["stats"]
    typer.echo(
        f"Built {stats['total_models']} models, "
        f"{stats['total_edges']} edges "
        f"({stats['cross_app_edges']} cross-app) "
        f"across {len(stats['apps'])} apps."
    )
    typer.echo(f"Cache: {store.path}")


@django_model_app.command("tui")
def django_model_tui(
    theme: str | None = typer.Option(
        None,
        "--theme",
        "-t",
        help="Theme name (e.g. netbox-dark, dracula).",
    ),
    netbox_root: Path = typer.Option(
        _DEFAULT_NETBOX_ROOT,
        "--netbox-root",
        "-n",
        help="Path to the NetBox Django project root (auto-builds if cache missing).",
    ),
    cache_path: Path | None = typer.Option(
        None,
        "--cache-path",
        "-o",
        help="Path to a specific model graph JSON file.",
    ),
) -> None:
    """Launch the Django Model Inspector TUI.

    Automatically builds the model cache if it doesn't exist.
    """
    from netbox_tui.django_model_app import run_django_model_tui  # noqa: PLC0415

    store = DjangoModelStore(cache_path=cache_path)
    if not store.exists():
        if not netbox_root.is_dir():
            typer.echo(f"Error: NetBox source not found at {netbox_root}", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"Model cache not found at {store.path}.")
        confirm = typer.confirm("Build it now? (this takes a few seconds)")
        if not confirm:
            typer.echo("Aborted. Run 'nbx dev django-model build' first.")
            raise typer.Exit(code=1)
        typer.echo("Building model cache...")
        store.build(netbox_root)
        typer.echo("Cache built.")

    run_django_model_tui(store=store, theme_name=theme)


@django_model_app.command("fetch")
def django_model_fetch(
    tag: str | None = typer.Argument(
        None,
        help="Release tag to fetch (e.g. v4.2.1). Omit with --auto to detect from connected NetBox.",
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        "-a",
        help="Detect NetBox version from the default profile and fetch the matching release.",
    ),
) -> None:
    """Fetch a NetBox release from GitHub and build the Django model graph.

    Examples::

        nbx dev django-model fetch v4.2.1
        nbx dev django-model fetch --auto
    """
    from netbox_sdk.django_models.fetcher import (  # noqa: PLC0415
        build_exists,
        clone_and_build,
        find_github_release_tag,
    )

    if auto:
        from netbox_cli.support import run_with_spinner  # noqa: PLC0415

        # Need a connected NetBox instance to detect the version.
        try:
            from netbox_cli.runtime import _ensure_runtime_config, _get_client  # noqa: PLC0415
        except ImportError:
            typer.echo(
                "Error: Could not import runtime. Is the default profile configured?", err=True
            )
            raise typer.Exit(code=1) from None

        _ensure_runtime_config()
        probe = run_with_spinner(_get_client().probe_connection())
        if not probe.ok:
            detail = probe.error or f"HTTP {probe.status}"
            typer.echo(f"Connection failed: {detail}", err=True)
            raise typer.Exit(code=1)
        if not probe.version:
            typer.echo("Could not detect NetBox API version.", err=True)
            raise typer.Exit(code=1)

        typer.echo(f"Detected NetBox API version: {probe.version}")
        resolved_tag = find_github_release_tag(probe.version)
        if resolved_tag is None:
            typer.echo(f"No GitHub release found for API version {probe.version}.", err=True)
            raise typer.Exit(code=1)
        tag = resolved_tag

    if tag is None:
        typer.echo("Error: provide a release tag or use --auto.", err=True)
        raise typer.Exit(code=1)

    if build_exists(tag):
        typer.echo(
            f"Build already exists for {tag}. Use 'nbx dev django-model build --rebuild' to refresh."
        )
        raise typer.Exit(code=0)

    clone_and_build(tag)
