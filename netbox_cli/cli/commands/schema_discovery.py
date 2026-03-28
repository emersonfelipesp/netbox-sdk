"""OpenAPI schema discovery commands: groups, resources, ops."""

from __future__ import annotations

import typer
from rich.table import Table

from ..support import console
from ._wiring import get_bound_index


def register_schema_discovery_commands(app: typer.Typer) -> None:
    @app.command("groups")
    def groups_command() -> None:
        """List all available OpenAPI app groups."""
        index = get_bound_index()
        for group in index.groups():
            typer.echo(group)

    @app.command("resources")
    def resources_command(
        group: str = typer.Argument(..., help="OpenAPI app group, e.g. dcim"),
    ) -> None:
        """List resources available within a group."""
        index = get_bound_index()
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
        """Show available HTTP operations for a resource."""
        index = get_bound_index()
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
