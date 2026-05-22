"""Internal decorators for shared CLI command execution patterns."""

from __future__ import annotations

import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Literal, ParamSpec, TypeVar

import typer

from netbox_cli.support import render_table, run_with_spinner
from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    BranchJobTimeoutError,
)

P = ParamSpec("P")
R = TypeVar("R")
CommandResource = TypeVar("CommandResource")

CommandOperation = Callable[[CommandResource], Awaitable[R]]
CommandResourceFactory = Callable[[], tuple[CommandResource, Any]]


@dataclass(frozen=True, slots=True)
class CliResultRenderer:
    """Rendering policy for a command result."""

    kind: Literal["json", "table", "message", "none"]
    columns: list[str] | None = None
    message: str | None = None
    max_columns: int = 6


def json_result() -> CliResultRenderer:
    return CliResultRenderer(kind="json")


def table_result(
    columns: list[str] | None = None,
    *,
    max_columns: int = 6,
) -> CliResultRenderer:
    return CliResultRenderer(kind="table", columns=columns, max_columns=max_columns)


def message_result(message: str) -> CliResultRenderer:
    return CliResultRenderer(kind="message", message=message)


def no_result() -> CliResultRenderer:
    return CliResultRenderer(kind="none")


async def _close_resource(resource: Any) -> None:
    close = getattr(resource, "close", None)
    if not callable(close):
        return
    result = close()
    if inspect.isawaitable(result):
        await result


async def _run_with_resource(
    resource_factory: CommandResourceFactory[CommandResource],
    operation: CommandOperation[CommandResource, R],
) -> R:
    resource, close_target = resource_factory()
    try:
        return await operation(resource)
    finally:
        await _close_resource(close_target)


def render_cli_result(value: Any, renderer: CliResultRenderer) -> None:
    if renderer.kind == "none":
        return
    if renderer.kind == "message":
        if renderer.message:
            typer.echo(renderer.message)
        return
    if renderer.kind == "table":
        render_table(value, columns=renderer.columns, max_columns=renderer.max_columns)
        return
    typer.echo(json.dumps(value, indent=2, default=str))


def raise_branching_cli_error(exc: Exception) -> None:
    if isinstance(exc, BranchingPluginUnavailableError):
        typer.echo(f"netbox-branching is not installed on this server: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    if isinstance(exc, BranchConflictError):
        typer.echo(f"Conflict reported by NetBox: {exc}", err=True)
        if exc.conflicts:
            typer.echo(json.dumps(exc.conflicts, indent=2, default=str), err=True)
        raise typer.Exit(code=3) from exc
    if isinstance(exc, BranchJobTimeoutError):
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=4) from exc
    raise exc


def resource_command(
    *,
    resource_factory: CommandResourceFactory[CommandResource],
    renderer: CliResultRenderer,
    error_handler: Callable[[Exception], None] | None = None,
) -> Callable[
    [Callable[P, CommandOperation[CommandResource, R]]],
    Callable[P, None],
]:
    """Run a returned async operation against a managed command resource."""

    def _decorator(
        func: Callable[P, CommandOperation[CommandResource, R]],
    ) -> Callable[P, None]:
        @wraps(func)
        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
            operation = func(*args, **kwargs)
            try:
                result = run_with_spinner(_run_with_resource(resource_factory, operation))
            except Exception as exc:
                if error_handler is not None:
                    error_handler(exc)
                raise
            render_cli_result(result, renderer)

        return _wrapper

    return _decorator
