"""Typer CLI entrypoints and command registration for the NetBox CLI application."""

from __future__ import annotations

import click
import typer

from ..config import load_profile_config as load_profile_config
from ..config import save_profile_config as save_profile_config
from ..logging_runtime import (
    log_file_path as log_file_path,
)
from ..logging_runtime import (
    read_log_entries as read_log_entries,
)
from ..logging_runtime import (
    setup_logging,
)
from ..services import run_dynamic_command as run_dynamic_command
from . import demo as demo
from .commands import register_static_commands
from .dynamic import _register_openapi_subcommands as _register_openapi_subcommands
from .runtime import (
    _RUNTIME_CONFIGS as _RUNTIME_CONFIGS,
)
from .runtime import (
    _cache_profile as _cache_profile,
)
from .runtime import (
    _ensure_demo_runtime_config as _ensure_demo_runtime_config,
)
from .runtime import (
    _ensure_runtime_config as _ensure_runtime_config,
)
from .runtime import (
    _get_client as _get_client,
)
from .runtime import (
    _get_client_for_config as _get_client_for_config,
)
from .runtime import (
    _get_demo_client as _get_demo_client,
)
from .runtime import (
    _get_index as _get_index,
)
from .runtime import (
    _verify_runtime_config as _verify_runtime_config,
)
from .support import emit_cli_error, format_click_exception

_initialize_demo_profile = demo._initialize_demo_profile

app = typer.Typer(
    add_completion=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="NetBox API-first CLI/TUI. Dynamic command form: nbx <group> <resource> <action>",
    no_args_is_help=True,
)

register_static_commands(app)


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


if __name__ == "__main__":
    raise SystemExit(main())
