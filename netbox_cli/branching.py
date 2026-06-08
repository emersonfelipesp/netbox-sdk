"""``nbx branching`` (and alias ``nbx branch``) commands for ``netbox-branching``.

Operates against the configured default NetBox profile via the SDK's
:class:`netbox_sdk.branching.BranchingClient`. Job-returning verbs accept
``--wait`` to block until the queued job finishes.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar

import typer

from netbox_cli.decorators import (
    CliResultRenderer,
    json_result,
    message_result,
    raise_branching_cli_error,
    resource_command,
    table_result,
)
from netbox_cli.runtime import _get_client
from netbox_sdk.branching import BranchingClient

branching_app = typer.Typer(
    add_completion=False,
    help="Manage netbox-branching plugin objects (branches, syncs, merges).",
    no_args_is_help=True,
)


BranchingOperation = Callable[[BranchingClient], Awaitable[Any]]
P = ParamSpec("P")
R = TypeVar("R")


def _branching_resource() -> tuple[BranchingClient, Any]:
    """Build a branching client for ad-hoc CLI use; caller closes the raw client.

    Uses :meth:`BranchingClient.from_client` so each branching command avoids
    building a full ``Api`` (and its schema index) it never uses.
    """
    raw = _get_client()
    return BranchingClient.from_client(raw), raw


def _branching_command(
    renderer: CliResultRenderer,
) -> Callable[
    [Callable[P, Callable[[BranchingClient], Awaitable[R]]]],
    Callable[P, None],
]:
    return resource_command(
        resource_factory=_branching_resource,
        renderer=renderer,
        error_handler=raise_branching_cli_error,
    )


def _resolve_id(value: str) -> int | str:
    return int(value) if value.isdigit() else value


@branching_app.command("status")
@_branching_command(json_result())
def cmd_status() -> BranchingOperation:
    """Check whether the netbox-branching plugin is installed."""

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        available = await client.is_available()
        result: dict[str, Any] = {"available": available}
        if available:
            try:
                branches = await client.list()
                result["branch_count"] = len(branches)
            except Exception as exc:  # noqa: BLE001
                result["branch_count_error"] = str(exc)
        return result

    return _run_async


@branching_app.command("list")
@_branching_command(table_result(columns=["id", "schema_id", "name", "status"]))
def cmd_list(
    status: str = typer.Option(None, "--status", help="Filter by branch status (e.g. ready)."),
    name: str = typer.Option(None, "--name", help="Filter by branch name."),
) -> Callable[[BranchingClient], Awaitable[list[dict[str, Any]]]]:
    """List branches."""

    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if name:
        filters["name"] = name

    return lambda client: client.list(**filters)


@branching_app.command("show")
@_branching_command(json_result())
def cmd_show(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
    """Show a single branch."""

    return lambda client: client.get(_resolve_id(id_or_schema))


@branching_app.command("create")
@_branching_command(json_result())
def cmd_create(
    name: str = typer.Option(..., "--name", help="Branch name."),
    description: str | None = typer.Option(None, "--description", help="Optional description."),
    comments: str | None = typer.Option(None, "--comments", help="Optional comments."),
) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
    """Create a branch."""

    fields: dict[str, Any] = {}
    if description is not None:
        fields["description"] = description
    if comments is not None:
        fields["comments"] = comments

    return lambda client: client.create(name, **fields)


@branching_app.command("update")
@_branching_command(json_result())
def cmd_update(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    name: str = typer.Option(None, "--name"),
    description: str = typer.Option(None, "--description"),
    comments: str = typer.Option(None, "--comments"),
) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
    """Patch branch fields."""

    fields: dict[str, Any] = {
        k: v
        for k, v in {"name": name, "description": description, "comments": comments}.items()
        if v is not None
    }
    if not fields:
        typer.echo("Provide at least one --name/--description/--comments to update.", err=True)
        raise typer.Exit(code=1)

    return lambda client: client.update(_resolve_id(id_or_schema), **fields)


@branching_app.command("delete")
@_branching_command(message_result("Branch deleted."))
def cmd_delete(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> Callable[[BranchingClient], Awaitable[None]]:
    """Delete a branch."""

    if not yes:
        if not typer.confirm(f"Delete branch {id_or_schema}?", default=False):
            raise typer.Exit(code=1)

    return lambda client: client.delete(_resolve_id(id_or_schema))


def _action_factory(verb: str) -> Callable[..., None]:
    @branching_app.command(verb)
    @_branching_command(json_result())
    def _cmd(  # noqa: ANN202
        id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
        commit: bool = typer.Option(
            True, "--commit/--no-commit", help="Apply changes (default true)."
        ),
        acknowledge_conflicts: bool = typer.Option(
            False,
            "--acknowledge-conflicts",
            help="Skip conflicting objects rather than raising.",
        ),
        wait: bool = typer.Option(
            True, "--wait/--no-wait", help="Wait for the background job to finish."
        ),
        timeout: float = typer.Option(600.0, "--timeout", help="Maximum seconds to wait."),
    ) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
        async def _run_async(client: BranchingClient) -> dict[str, Any]:
            method = getattr(client, verb)
            return await method(
                _resolve_id(id_or_schema),
                commit=commit,
                acknowledge_conflicts=acknowledge_conflicts,
                wait=wait,
                timeout=timeout,
            )

        return _run_async

    _cmd.__doc__ = f"Queue a {verb} on the branch."
    _cmd.__name__ = f"cmd_{verb}"
    return _cmd


_action_factory("sync")
_action_factory("merge")


@branching_app.command("revert")
@_branching_command(json_result())
def cmd_revert(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    wait: bool = typer.Option(True, "--wait/--no-wait"),
    timeout: float = typer.Option(600.0, "--timeout"),
) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
    """Revert a previously-merged branch."""

    return lambda client: client.revert(_resolve_id(id_or_schema), wait=wait, timeout=timeout)


@branching_app.command("archive")
@_branching_command(json_result())
def cmd_archive(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> Callable[[BranchingClient], Awaitable[dict[str, Any]]]:
    """Archive a branch (synchronous server-side)."""

    if not yes:
        if not typer.confirm(f"Archive branch {id_or_schema}?", default=False):
            raise typer.Exit(code=1)

    return lambda client: client.archive(_resolve_id(id_or_schema))


@branching_app.command("events")
@_branching_command(table_result(columns=["id", "branch", "type", "user", "time"]))
def cmd_events(
    branch: str = typer.Option(None, "--branch", help="Filter by branch PK or schema_id."),
    type_: str = typer.Option(None, "--type", help="Event type filter (e.g. synced, merged)."),
) -> Callable[[BranchingClient], Awaitable[list[dict[str, Any]]]]:
    """List branch events."""

    filters: dict[str, Any] = {}
    if branch:
        filters["branch"] = branch
    if type_:
        filters["type"] = type_

    return lambda client: client.events(**filters)


@branching_app.command("changes")
@_branching_command(table_result())
def cmd_changes(
    branch: str = typer.Option(None, "--branch"),
    action: str = typer.Option(None, "--action", help="create / update / delete"),
    has_conflicts: bool = typer.Option(False, "--has-conflicts"),
) -> Callable[[BranchingClient], Awaitable[list[dict[str, Any]]]]:
    """List recorded change-diffs."""

    filters: dict[str, Any] = {}
    if branch:
        filters["branch"] = branch
    if action:
        filters["action"] = action
    if has_conflicts:
        filters["has_conflicts"] = "true"

    return lambda client: client.changes(**filters)


@branching_app.command("models")
@_branching_command(table_result())
def cmd_models() -> Callable[[BranchingClient], Awaitable[list[dict[str, Any]]]]:
    """List branchable models."""

    return lambda client: client.branchable_models()


__all__ = ["branching_app"]
