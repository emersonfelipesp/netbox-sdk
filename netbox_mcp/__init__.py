"""Explicit schema-driven MCP server for netbox-sdk."""

from __future__ import annotations

import argparse
import os
from typing import TYPE_CHECKING

from netbox_mcp.app import (
    AUTH_TOKEN_ENV_VAR,
    build_streamable_http_app,
    create_mcp_server,
)
from netbox_mcp.service import MUTATION_ENV_VAR, NetBoxMCPService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

__all__ = ["MUTATION_ENV_VAR", "NetBoxMCPService", "create_mcp_server", "run"]


async def _run_streamable_http(
    server: FastMCP, *, host: str, port: int, auth_token: str | None
) -> None:
    import uvicorn

    app = build_streamable_http_app(server, auth_token=auth_token)
    config = uvicorn.Config(app, host=host, port=port, log_level=server.settings.log_level.lower())
    await uvicorn.Server(config).serve()


def run(argv: list[str] | None = None) -> None:
    """Run the MCP server over stdio (default) or Streamable HTTP."""
    parser = argparse.ArgumentParser(description="Schema-driven NetBox MCP server")
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Streamable HTTP bind host")
    parser.add_argument("--port", type=int, default=8000, help="Streamable HTTP bind port")
    parser.add_argument(
        "--auth-token",
        default=None,
        help=(
            "Shared-secret bearer token required of every Streamable HTTP caller "
            f"(equivalent to {AUTH_TOKEN_ENV_VAR}). Required for every bind host, "
            "including loopback: binding to 127.0.0.1 only restricts reachability "
            "to this machine, it does not authenticate other local processes or "
            "users."
        ),
    )
    parser.add_argument(
        "--allow-mutations",
        action="store_true",
        default=None,
        help=f"Enable write tools (equivalent to {MUTATION_ENV_VAR}=1)",
    )
    args = parser.parse_args(argv)
    service = NetBoxMCPService(allow_mutations=args.allow_mutations)
    if args.transport == "streamable-http":
        import anyio

        auth_token = args.auth_token or os.environ.get(AUTH_TOKEN_ENV_VAR)
        if not auth_token:
            # Binding to a loopback host restricts *reachability* to this
            # machine, but does not *authenticate* the caller: any other
            # process or user on a shared dev/bastion host can still connect
            # and act with this server's loaded NetBox credential (and any
            # active --allow-mutations window). Require a token unconditionally.
            raise RuntimeError(
                f"Refusing to bind Streamable HTTP to host {args.host!r} without "
                f"an auth token. Set --auth-token or {AUTH_TOKEN_ENV_VAR} — this "
                "is required even for loopback hosts."
            )
        server = create_mcp_server(service, host=args.host, port=args.port, auth_token=auth_token)
        anyio.run(
            lambda: _run_streamable_http(
                server, host=args.host, port=args.port, auth_token=auth_token
            )
        )
    else:
        server = create_mcp_server(service, host=args.host, port=args.port)
        server.run(transport=args.transport)
