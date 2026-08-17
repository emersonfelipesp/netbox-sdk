"""Explicit schema-driven MCP server for netbox-sdk."""

from __future__ import annotations

import argparse
import os
from collections.abc import Mapping
from typing import TYPE_CHECKING

from netbox_mcp.app import (
    AUTH_TOKEN_ENV_VAR,
    build_streamable_http_app,
    create_mcp_server,
)
from netbox_mcp.service import MUTATION_ENV_VAR, NetBoxMCPService
from netbox_sdk.schema_resolution import requested_netbox_version
from netbox_sdk.versioning import describe_supported_versions, normalize_netbox_version

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

__all__ = ["MUTATION_ENV_VAR", "NetBoxMCPService", "create_mcp_server", "run"]


DEDICATED_VERSION_ENV_VAR = "NETBOX_SDK_NETBOX_VERSION"
# Broader, historically-accepted aliases. These names are generic enough that an
# unrelated deployment may already define them for its own purposes, so they are
# read leniently: an unusable value is ignored with a warning rather than being
# treated as an operator instruction.
LEGACY_VERSION_ENV_VARS = ("NETBOX_API_VERSION", "NETBOX_VERSION")


def _resolve_startup_pin(flag_value: str | None, env: Mapping[str, str]) -> str | None:
    """Resolve the release-line pin for a server start.

    The entrypoint is the only place that reads the documented pin sources; the
    service never touches process globals. When ``run(argv=...)`` supplied an
    argument list, ambient ``sys.argv`` is not consulted either, so an embedding
    host's own flags cannot repoint this server.

    Strictness is deliberately split:

    * an explicit ``--netbox-version``/``--api-version`` flag and the dedicated
      ``NETBOX_SDK_NETBOX_VERSION`` variable are **operator instructions**, so an
      unusable value fails startup - quietly serving a different release line
      than the operator asked for is worse than refusing to start;
    * ``NETBOX_API_VERSION`` and ``NETBOX_VERSION`` are generic names an
      unrelated environment may already define (a compose file pinning the NetBox
      *server* version, say), so an unusable value there is ignored with a
      warning instead of blocking startup.

    Raises:
        UnsupportedNetBoxVersionError: If an explicit flag or the dedicated
            environment variable names an unsupported release line.
    """
    if flag_value is not None:
        return normalize_netbox_version(flag_value)
    dedicated = env.get(DEDICATED_VERSION_ENV_VAR)
    if dedicated:
        return normalize_netbox_version(dedicated)
    legacy = {name: env[name] for name in LEGACY_VERSION_ENV_VARS if env.get(name)}
    return requested_netbox_version([], legacy, strict=False)


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
    parser.add_argument(
        "--netbox-version",
        "--api-version",
        dest="netbox_version",
        default=None,
        help=(
            "Pin the bundled NetBox release line used for schema resolution "
            f"({describe_supported_versions()})."
        ),
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
    pinned_line = _resolve_startup_pin(args.netbox_version, os.environ)
    service = NetBoxMCPService(
        allow_mutations=args.allow_mutations,
        pinned_line=pinned_line,
    )
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
