"""Register static Typer commands on the root ``nbx`` app."""

from __future__ import annotations

import typer

from ..demo import demo_app
from ..dev import dev_app
from ..dynamic import _register_openapi_subcommands
from .http_api import register_http_api_commands
from .profile import register_profile_commands
from .root import register_root_callback
from .schema_discovery import register_schema_discovery_commands
from .subapps import build_cli_builder_app, build_docs_app
from .tui_launch import register_tui_launch_commands


def _demo_openapi_client_factory():
    from netbox_cli.cli import (  # noqa: PLC0415
        _ensure_demo_runtime_config,
        _get_client_for_config,
    )

    return _get_client_for_config(_ensure_demo_runtime_config())


def _demo_openapi_index_factory():
    from netbox_cli.cli import _get_index as gi  # noqa: PLC0415

    return gi()


def register_static_commands(app: typer.Typer) -> None:
    register_root_callback(app)
    register_profile_commands(app)
    register_schema_discovery_commands(app)
    register_http_api_commands(app)
    register_tui_launch_commands(app)

    cli_builder_app = build_cli_builder_app()
    docs_cmd_app = build_docs_app()
    app.add_typer(cli_builder_app, name="cli")
    app.add_typer(docs_cmd_app, name="docs")
    app.add_typer(demo_app, name="demo")
    app.add_typer(dev_app, name="dev")

    _register_openapi_subcommands(app)
    _register_openapi_subcommands(
        demo_app,
        client_factory=_demo_openapi_client_factory,
        index_factory=_demo_openapi_index_factory,
    )
