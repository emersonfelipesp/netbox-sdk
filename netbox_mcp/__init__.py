"""Explicit schema-driven MCP server for netbox-sdk."""

from __future__ import annotations

import argparse

from netbox_mcp.app import create_mcp_server
from netbox_mcp.service import MUTATION_ENV_VAR, NetBoxMCPService

__all__ = ["MUTATION_ENV_VAR", "NetBoxMCPService", "create_mcp_server", "run"]


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
        "--allow-mutations",
        action="store_true",
        default=None,
        help=f"Enable write tools (equivalent to {MUTATION_ENV_VAR}=1)",
    )
    args = parser.parse_args(argv)
    service = NetBoxMCPService(allow_mutations=args.allow_mutations)
    server = create_mcp_server(service, host=args.host, port=args.port)
    server.run(transport=args.transport)
