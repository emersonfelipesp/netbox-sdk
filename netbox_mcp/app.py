"""FastMCP adapter for the transport-independent NetBox MCP service."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from netbox_mcp.service import NetBoxMCPService

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send

AUTH_TOKEN_ENV_VAR = "NETBOX_MCP_AUTH_TOKEN"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def is_loopback_host(host: str) -> bool:
    """Return whether ``host`` is a loopback bind address."""
    return host in _LOOPBACK_HOSTS


class BearerTokenMiddleware:
    """Raw ASGI middleware enforcing a static shared-secret bearer token.

    Implemented as plain ASGI rather than Starlette's ``BaseHTTPMiddleware``,
    which buffers the entire response body and breaks the Streamable HTTP
    transport's long-lived streaming responses.
    """

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        request = Request(scope)
        scheme, _, credential = request.headers.get("authorization", "").partition(" ")
        if (
            scheme.lower() != "bearer"
            or not credential
            or not secrets.compare_digest(credential, self._token)
        ):
            response = JSONResponse({"error": "unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return
        await self._app(scope, receive, send)


def build_streamable_http_app(server: FastMCP, *, auth_token: str | None) -> ASGIApp:
    """Return the server's Streamable HTTP ASGI app, always gated by ``auth_token``.

    Rebuilds from ``FastMCP.streamable_http_app`` (the class method) rather
    than ``server.streamable_http_app`` (the instance attribute), because
    ``create_mcp_server`` shadows the latter with this same wrapped app to
    close the direct-call bypass described there. Calling the class method
    here instead avoids re-wrapping an already-wrapped app or recursing back
    into this function.
    """
    if not auth_token:
        raise RuntimeError(
            "Refusing to build a Streamable HTTP app without an auth_token — "
            "an unauthenticated app would expose the configured NetBox "
            "credential and any active mutation window to every reachable caller."
        )
    app: ASGIApp = FastMCP.streamable_http_app(server)
    return BearerTokenMiddleware(app, auth_token)


def build_sse_app(
    server: FastMCP, *, auth_token: str | None, mount_path: str | None = None
) -> ASGIApp:
    """Return the server's SSE ASGI app, always gated by ``auth_token``.

    Mirrors :func:`build_streamable_http_app`. ``FastMCP.sse_app`` (used by
    both ``server.sse_app()`` and ``server.run("sse")`` /
    ``run_sse_async()``) mounts its SSE and message-post routes completely
    unauthenticated whenever no token verifier is configured on the
    instance — which this codebase never sets — so this wrapper is the only
    auth gate for the SSE transport. ``mount_path`` is forwarded to
    ``FastMCP.sse_app`` for parity with ``run_sse_async(mount_path)``.
    """
    if not auth_token:
        raise RuntimeError(
            "Refusing to build an SSE app without an auth_token — an "
            "unauthenticated app would expose the configured NetBox "
            "credential and any active mutation window to every reachable caller."
        )
    app: ASGIApp = FastMCP.sse_app(server, mount_path)
    return BearerTokenMiddleware(app, auth_token)


def create_mcp_server(
    service: NetBoxMCPService | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    auth_token: str | None = None,
) -> FastMCP:
    """Create a stateless JSON FastMCP server with the explicit NetBox tools.

    The returned server's ``streamable_http_app`` and ``sse_app`` instance
    attributes always shadow their class methods with ones that route
    through :func:`build_streamable_http_app` / :func:`build_sse_app`, both
    of which require a non-empty ``auth_token``. This closes the bypass
    where calling ``server.streamable_http_app()``,
    ``server.run("streamable-http")``, ``server.sse_app()``, or
    ``server.run("sse")`` directly — instead of going through this module's
    own transport helpers — would otherwise start an unauthenticated
    network server: with no ``auth_token`` configured here, every one of
    those calls now raises ``RuntimeError`` instead of silently binding
    unauthenticated.
    """
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

    server.streamable_http_app = lambda: build_streamable_http_app(  # type: ignore[method-assign]
        server, auth_token=auth_token
    )
    server.sse_app = lambda mount_path=None: build_sse_app(  # type: ignore[method-assign]
        server, auth_token=auth_token, mount_path=mount_path
    )

    return server
