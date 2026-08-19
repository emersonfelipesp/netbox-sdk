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
- Ordinary mutation `dry_run` resolves the local request only and must not
  construct a client. `plugin_call_tool` is the explicit exception: its dry-run
  uses a client for read-only plugin-root/manifest discovery, but must never
  dispatch the advertised target mutation. Neither form is server-side
  validation.
- All NetBox traffic must use `netbox_sdk.client.NetBoxApiClient`.
- Reuse `netbox_sdk.config` for static stdio credentials; do not add another
  credential store.
- Resolve the default and live schema indexes through
  `netbox_sdk.schema_resolution`; MCP version pins must select the same bundled
  line a CLI pin would.
- **The service never reads process globals for the version pin.**
  `NetBoxMCPService(pinned_line=...)` takes it as an explicit argument, resolves
  it once in `__init__`, and reuses it for both the default index and
  `_live_index`. Only the `nbx-mcp` entrypoint reads the documented pin sources
  and injects the result. An embedded host carrying its own `--api-version` flag
  must never repoint this server's schema.
- **Startup pin strictness is deliberately split** (`_resolve_startup_pin`).
  `--netbox-version`/`--api-version` and the dedicated
  `NETBOX_SDK_NETBOX_VERSION` are *operator instructions*: an unsupported value
  raises `UnsupportedNetBoxVersionError` and the server refuses to start, because
  quietly serving a different release line than the operator asked for is worse.
  `NETBOX_API_VERSION` and `NETBOX_VERSION` are generic names an unrelated
  deployment may already define (e.g. pinning the NetBox *server* image), so an
  unsupported value there is warned about and ignored rather than blocking
  startup.
- **Live resolution failures are raised, not swallowed.** `_live_index` calls
  `resolve_index` with `fall_back_on_error` left off, so an unreachable or
  misbehaving instance surfaces the error instead of quietly serving the default
  bundled contract for a server it cannot actually describe.
- **An unpinned server resolves the connected release line, once, lazily.**
  `_dispatch_index()` is the single chokepoint for what contract a tool call
  dispatches against:
  - An injected `index=` or an explicit `pinned_line=` **is** the declared
    contract and is returned unchanged — nothing is detected.
  - Otherwise the connected instance's line is detected on **first dispatch**,
    not in `__init__`, so a server is still constructible while NetBox is
    unreachable, and the result is cached for the life of the service (an
    `asyncio.Lock` with a re-check means concurrent first calls detect once, not
    N times). This mirrors the CLI resolving once per invocation rather than per
    command.
  - It **fails closed**: `fall_back_on_error=False`, so a detection failure or a
    non-OpenAPI document fails the tool call. A failed attempt is never cached,
    so a transient outage does not poison the server for its lifetime.
  - **Ordering with the mutation gate matters.** `_mutate` resolves the contract
    *before* `_ensure_mutations_allowed()`, because a write dispatched against a
    mis-detected contract is the worst outcome available.
  - **`dry_run` stays client-free** and previews from the declared/bundled
    contract. Acquiring a connection just to render a local preview would defeat
    the point of the preview; this is documented as a local request preview, not
    server-side validation.
  - `filters` remains local-only and bundled-contract by design: it takes no
    token, so it has nothing to authenticate a live resolution with, and #44
    specifies it as a no-HTTP tool.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Public exports, argument parsing, and `nbx-mcp` entrypoint |
| `__main__.py` | `python -m netbox_mcp` launcher |
| `app.py` | Explicit FastMCP tool registration and transport adapter |
| `models.py` | Strict Pydantic input schemas for every tool family |
| `service.py` | Transport-independent schema introspection through the shared SDK resolver, reads, writes, plugin discovery, bounded/non-redirecting semantic plugin bridge dispatch, strict response parsing, auth, and mutation gate |
| `py.typed` | PEP 561 marker |

## Import Rules

- Use `netbox_sdk.introspection` for contracts shared with CLI JSON output.
- Use `netbox_sdk.services.resolve_dynamic_request` for every named operation.
- Use `netbox_sdk.services.list_all_pages` for `list(all=true)`.
- Use `netbox_sdk.plugin_discovery` for live plugin resources.
- Use `netbox_sdk.schema_resolution` for version overrides and bundled/live
  index selection; do not parse version environment variables or detect release
  lines locally.
- Use `netbox_sdk.plugin_bridge` for advertised semantic plugin tools; never
  resolve their paths or JSON Schemas independently in the MCP package.
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
