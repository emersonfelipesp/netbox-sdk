"""``nbx branching`` (and alias ``nbx branch``) commands for ``netbox-branching``.

Operates against the configured default NetBox profile via the SDK's
:class:`netbox_sdk.branching.BranchingClient`. Job-returning verbs accept
``--wait`` to block until the queued job finishes.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import typer

from netbox_cli.runtime import _get_client
from netbox_cli.support import render_table, run_with_spinner
from netbox_sdk.branching import BranchingClient
from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    BranchJobTimeoutError,
)
from netbox_sdk.facade import Api

branching_app = typer.Typer(
    add_completion=False,
    help="Manage netbox-branching plugin objects (branches, syncs, merges).",
    no_args_is_help=True,
)


def _client() -> tuple[Api, Any]:
    """Build an :class:`Api` for ad-hoc CLI use; caller closes the underlying client."""
    raw = _get_client()
    api = Api(client=raw)
    return api, raw


async def _close(raw: Any) -> None:
    close = getattr(raw, "close", None)
    if callable(close):
        result = close()
        if hasattr(result, "__await__"):
            await result


async def _with_branching(coro_factory: Any) -> Any:
    api, raw = _client()
    try:
        return await coro_factory(api.branching)
    finally:
        await _close(raw)


def _run(coro_factory: Any) -> Any:
    """Resolve a coroutine factory using the configured NetBox profile."""
    try:
        return run_with_spinner(_with_branching(coro_factory))
    except BranchingPluginUnavailableError as exc:
        typer.echo(f"netbox-branching is not installed on this server: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except BranchConflictError as exc:
        typer.echo(f"Conflict reported by NetBox: {exc}", err=True)
        if exc.conflicts:
            typer.echo(json.dumps(exc.conflicts, indent=2, default=str), err=True)
        raise typer.Exit(code=3) from exc
    except BranchJobTimeoutError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=4) from exc


def _resolve_id(value: str) -> int | str:
    return int(value) if value.isdigit() else value


@branching_app.command("status")
def cmd_status() -> None:
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

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2))


@branching_app.command("list")
def cmd_list(
    status: str = typer.Option(None, "--status", help="Filter by branch status (e.g. ready)."),
    name: str = typer.Option(None, "--name", help="Filter by branch name."),
) -> None:
    """List branches."""

    filters: dict[str, Any] = {}
    if status:
        filters["status"] = status
    if name:
        filters["name"] = name

    async def _run_async(client: BranchingClient) -> list[dict[str, Any]]:
        return await client.list(**filters)

    rows = _run(_run_async)
    render_table(rows, columns=["id", "schema_id", "name", "status"])


@branching_app.command("show")
def cmd_show(id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id.")) -> None:
    """Show a single branch."""

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        return await client.get(_resolve_id(id_or_schema))

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2, default=str))


@branching_app.command("create")
def cmd_create(
    name: str = typer.Option(..., "--name", help="Branch name."),
    description: str = typer.Option("", "--description", help="Optional description."),
    comments: str = typer.Option("", "--comments", help="Optional comments."),
) -> None:
    """Create a branch."""

    fields: dict[str, Any] = {}
    if description:
        fields["description"] = description
    if comments:
        fields["comments"] = comments

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        return await client.create(name, **fields)

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2, default=str))


@branching_app.command("update")
def cmd_update(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    name: str = typer.Option(None, "--name"),
    description: str = typer.Option(None, "--description"),
    comments: str = typer.Option(None, "--comments"),
) -> None:
    """Patch branch fields."""

    fields: dict[str, Any] = {
        k: v
        for k, v in {"name": name, "description": description, "comments": comments}.items()
        if v is not None
    }
    if not fields:
        typer.echo("Provide at least one --name/--description/--comments to update.", err=True)
        raise typer.Exit(code=1)

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        return await client.update(_resolve_id(id_or_schema), **fields)

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2, default=str))


@branching_app.command("delete")
def cmd_delete(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Delete a branch."""

    if not yes:
        if not typer.confirm(f"Delete branch {id_or_schema}?", default=False):
            raise typer.Exit(code=1)

    async def _run_async(client: BranchingClient) -> None:
        await client.delete(_resolve_id(id_or_schema))

    _run(_run_async)
    typer.echo("Branch deleted.")


def _action_factory(verb: str) -> Callable[..., None]:
    @branching_app.command(verb)
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
    ) -> None:
        f"""Queue a {verb} on the branch."""

        async def _run_async(client: BranchingClient) -> dict[str, Any]:
            method = getattr(client, verb)
            return await method(
                _resolve_id(id_or_schema),
                commit=commit,
                acknowledge_conflicts=acknowledge_conflicts,
                wait=wait,
                timeout=timeout,
            )

        payload = _run(_run_async)
        typer.echo(json.dumps(payload, indent=2, default=str))

    _cmd.__name__ = f"cmd_{verb}"
    return _cmd


_action_factory("sync")
_action_factory("merge")


@branching_app.command("revert")
def cmd_revert(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    wait: bool = typer.Option(True, "--wait/--no-wait"),
    timeout: float = typer.Option(600.0, "--timeout"),
) -> None:
    """Revert a previously-merged branch."""

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        return await client.revert(_resolve_id(id_or_schema), wait=wait, timeout=timeout)

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2, default=str))


@branching_app.command("archive")
def cmd_archive(
    id_or_schema: str = typer.Argument(..., help="Branch PK or schema_id."),
    yes: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Archive a branch (synchronous server-side)."""

    if not yes:
        if not typer.confirm(f"Archive branch {id_or_schema}?", default=False):
            raise typer.Exit(code=1)

    async def _run_async(client: BranchingClient) -> dict[str, Any]:
        return await client.archive(_resolve_id(id_or_schema))

    payload = _run(_run_async)
    typer.echo(json.dumps(payload, indent=2, default=str))


@branching_app.command("events")
def cmd_events(
    branch: str = typer.Option(None, "--branch", help="Filter by branch PK or schema_id."),
    type_: str = typer.Option(None, "--type", help="Event type filter (e.g. synced, merged)."),
) -> None:
    """List branch events."""

    filters: dict[str, Any] = {}
    if branch:
        filters["branch"] = branch
    if type_:
        filters["type"] = type_

    async def _run_async(client: BranchingClient) -> list[dict[str, Any]]:
        return await client.events(**filters)

    rows = _run(_run_async)
    render_table(rows, columns=["id", "branch", "type", "user", "time"])


@branching_app.command("changes")
def cmd_changes(
    branch: str = typer.Option(None, "--branch"),
    action: str = typer.Option(None, "--action", help="create / update / delete"),
    has_conflicts: bool = typer.Option(False, "--has-conflicts"),
) -> None:
    """List recorded change-diffs."""

    filters: dict[str, Any] = {}
    if branch:
        filters["branch"] = branch
    if action:
        filters["action"] = action
    if has_conflicts:
        filters["has_conflicts"] = "true"

    async def _run_async(client: BranchingClient) -> list[dict[str, Any]]:
        return await client.changes(**filters)

    rows = _run(_run_async)
    render_table(rows)


@branching_app.command("models")
def cmd_models() -> None:
    """List branchable models."""

    async def _run_async(client: BranchingClient) -> list[dict[str, Any]]:
        return await client.branchable_models()

    rows = _run(_run_async)
    render_table(rows)


__all__ = ["branching_app"]
