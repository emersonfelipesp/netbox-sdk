"""FastMCP adapter for the transport-independent NetBox MCP service."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from netbox_mcp.service import NetBoxMCPService


def create_mcp_server(
    service: NetBoxMCPService | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastMCP:
    """Create a stateless JSON FastMCP server with the explicit NetBox tools."""
    active = service or NetBoxMCPService()
    server = FastMCP(
        "netbox-sdk",
        instructions=(
            "Inspect groups, resources, and operations before calling NetBox. "
            "Preview every write with dry_run before enabling and executing mutations."
        ),
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
    )

    @server.tool()
    async def list_groups(live: bool = False, token: str | None = None) -> dict[str, Any]:
        """List schema groups; live mode adds resources discovered from the configured instance."""
        return await active.list_groups(live=live, token=token)

    @server.tool()
    async def list_resources(
        group: str, live: bool = False, token: str | None = None
    ) -> dict[str, Any]:
        """List resources in one group using the shared CLI JSON contract."""
        return await active.list_resources(group=group, live=live, token=token)

    @server.tool()
    async def describe_operation(
        group: str,
        resource: str,
        live: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Describe a resource's operations and filter parameters."""
        return await active.describe_operation(
            group=group, resource=resource, live=live, token=token
        )

    @server.tool(name="list")
    async def list_records(
        group: str,
        resource: str,
        query: list[str] | None = None,
        all: bool = False,
        max_records: int = 10_000,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """List NetBox records, optionally following all pagination links."""
        return await active.list(
            group=group,
            resource=resource,
            query=query,
            all=all,
            max_records=max_records,
            header=header,
            token=token,
        )

    @server.tool()
    async def get(
        group: str,
        resource: str,
        id: int,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Get one NetBox record by positive integer ID."""
        return await active.get(group=group, resource=resource, id=id, header=header, token=token)

    @server.tool()
    def filters(group: str, resource: str) -> dict[str, Any]:
        """List local schema filter parameters without making an HTTP request."""
        return active.filters(group=group, resource=resource)

    @server.tool()
    async def create(
        group: str,
        resource: str,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Create a record. dry_run is a local preview, not server validation or proof of success."""
        return await active.create(**locals())

    @server.tool()
    async def update(
        group: str,
        resource: str,
        id: int,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Replace a record. dry_run is a local preview, not server validation or proof of success."""
        return await active.update(**locals())

    @server.tool()
    async def patch(
        group: str,
        resource: str,
        id: int,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Patch a record. dry_run is a local preview, not server validation or proof of success."""
        return await active.patch(**locals())

    @server.tool()
    async def delete(
        group: str,
        resource: str,
        id: int,
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Delete a record. dry_run is a local preview, not server validation or proof of success."""
        return await active.delete(**locals())

    @server.tool()
    async def bulk_update(
        group: str,
        resource: str,
        payload: list[dict[str, Any]],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Bulk replace records. dry_run is a local preview, not server validation or proof of success."""
        return await active.bulk_update(**locals())

    @server.tool()
    async def bulk_patch(
        group: str,
        resource: str,
        payload: list[dict[str, Any]],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Bulk patch records. dry_run is a local preview, not server validation or proof of success."""
        return await active.bulk_patch(**locals())

    @server.tool()
    async def bulk_delete(
        group: str,
        resource: str,
        payload: list[dict[str, Any]],
        dry_run: bool = False,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Bulk delete records. dry_run is a local preview, not server validation or proof of success."""
        return await active.bulk_delete(**locals())

    @server.tool()
    async def plugin_discover(plugin: str, token: str | None = None) -> dict[str, Any]:
        """Discover live plugin resources and retain them in this server's schema index."""
        return await active.plugin_discover(plugin=plugin, token=token)

    @server.tool()
    async def call(
        method: str,
        path: str,
        query: list[str] | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        header: list[str] | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Call a relative /api/ path; only GET and HEAD are allowed until mutations are enabled."""
        return await active.call(
            method=method,
            path=path,
            query=query,
            payload=payload,
            header=header,
            token=token,
        )

    return server
