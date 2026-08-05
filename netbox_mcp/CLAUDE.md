# netbox_mcp — MCP Package

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_mcp/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

`netbox_mcp` is the optional Model Context Protocol adapter. It exposes a small,
schema-driven tool grammar over `netbox_sdk` instead of generating one tool per
OpenAPI operation.

## Package Contract

- Import only from `netbox_sdk.*` and `netbox_mcp.*`; never import `netbox_cli`
  or `netbox_tui`.
- Keep argument validation in strict Pydantic models before SDK dispatch.
- Keep live mutations disabled unless `NETBOX_MCP_ALLOW_MUTATIONS=1` or
  `--allow-mutations` is set explicitly.
- A mutation `dry_run` resolves the local request only. It must not construct a
  client or be described as server-side validation.
- All NetBox traffic must use `netbox_sdk.client.NetBoxApiClient`.
- Reuse `netbox_sdk.config` for static stdio credentials; do not add another
  credential store.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Public exports, argument parsing, and `nbx-mcp` entrypoint |
| `__main__.py` | `python -m netbox_mcp` launcher |
| `app.py` | Explicit FastMCP tool registration and transport adapter |
| `models.py` | Strict Pydantic input schemas for every tool family |
| `service.py` | Transport-independent schema introspection, reads, writes, plugin discovery, auth, and mutation gate |
| `py.typed` | PEP 561 marker |

## Import Rules

- Use `netbox_sdk.introspection` for contracts shared with CLI JSON output.
- Use `netbox_sdk.services.resolve_dynamic_request` for every named operation.
- Use `netbox_sdk.services.list_all_pages` for `list(all=true)`.
- Use `netbox_sdk.plugin_discovery` for live plugin resources.
- Keep MCP SDK imports in this optional package so `import netbox_sdk` remains
  valid without the `mcp` extra.

## Packaging

- Console entrypoint: `nbx-mcp = netbox_mcp:run`
- Extra required for this package: `.[mcp]`
- Default transport: stdio
- Optional transport: `nbx-mcp --transport streamable-http`
- Ownership test marker: `suite_mcp`

## Streamable HTTP Auth

`nbx-mcp --transport streamable-http` is gated by a shared-secret bearer
token, since Streamable HTTP is the transport used when the server is
network-reachable rather than spawned as a local stdio subprocess.

- Set the token via `--auth-token <value>` or `NETBOX_MCP_AUTH_TOKEN`
  (`--auth-token` wins if both are set). Prefer `NETBOX_MCP_AUTH_TOKEN` on any
  shared host: an argument's value is visible to other local users through
  `ps` and `/proc/<pid>/cmdline`, while the environment variable is not.
  `README.md` and `docs/mcp/index.md` document the invocation as
  `NETBOX_MCP_AUTH_TOKEN=<value> nbx-mcp --transport streamable-http ...`
  for this reason, never `--auth-token "$NETBOX_MCP_AUTH_TOKEN"`.
- Every `--host` value, including loopback (`127.0.0.1`, `localhost`,
  `::1`), requires a configured token — without one, `run()` raises
  `RuntimeError` before the server binds. There is no unauthenticated mode
  for this transport. Binding to loopback only restricts *reachability* to
  the local machine; it does not *authenticate* other local processes or
  users, who could otherwise reach the server's loaded NetBox credential
  (and any active `--allow-mutations` window) on a shared dev or bastion
  host.
- Enforcement is a raw ASGI middleware (`netbox_mcp.app.BearerTokenMiddleware`)
  wrapping `FastMCP.streamable_http_app()`, not Starlette's
  `BaseHTTPMiddleware`, because `BaseHTTPMiddleware` buffers the full
  response body and breaks Streamable HTTP's long-lived streaming
  responses. Callers must send `Authorization: Bearer <token>`; failures
  return `401`.
- The middleware wrapping is not opt-in at the call site: `create_mcp_server()`
  unconditionally shadows the returned `FastMCP` instance's
  `streamable_http_app` **instance attribute** with a closure over
  `build_streamable_http_app(server, auth_token=...)`, including when
  `auth_token` is `None`. `FastMCP.run(transport="streamable-http")` calls
  `self.streamable_http_app()` internally, and Python resolves an instance
  attribute before the class method of the same name — so both a direct
  `server.streamable_http_app()` call and `server.run("streamable-http")`
  are routed through the same auth gate as `_run_streamable_http()`, and
  both raise `RuntimeError` instead of silently serving an unauthenticated
  app when no token is configured. There is no `create_mcp_server()`-produced
  server instance capable of exposing an unauthenticated Streamable HTTP app.
- The same shadowing applies to the **SSE transport**: `create_mcp_server()`
  also shadows the instance's `sse_app` attribute with a closure over
  `build_sse_app(server, auth_token=..., mount_path=...)`. `FastMCP.sse_app()`
  mounts its SSE and message-post routes with zero auth wrapping of its own
  whenever no token verifier is configured on the instance — which this
  codebase never sets — so `server.sse_app()`, `server.run("sse")`, and
  `run_sse_async()` (which all resolve to the same instance attribute) are
  routed through `build_sse_app` exactly like the Streamable HTTP path. The
  `nbx-mcp` CLI entrypoint's `--transport` flag only exposes `stdio` and
  `streamable-http`, so this closes a bypass reachable only by code holding
  the `FastMCP` instance returned by `create_mcp_server()` directly, not by
  the CLI itself — but that instance is a public return value, so the gate
  still has to hold for it.
