# MCP Server

`netbox_mcp` provides a deliberately small Model Context Protocol surface over
the same `SchemaIndex`, request resolver, plugin discovery, pagination, client,
and profile configuration used by the SDK and CLI. It does not generate one
tool per OpenAPI operation, so its tool list stays stable when NetBox plugins
change the reachable resources.

## Which NetBox contract the server uses

A server started **without** a version pin detects the connected instance's
release line on its first tool call and uses that contract from then on. It is
detected once per server, lazily, so the server still starts while NetBox is
unreachable.

Detection **fails closed**: if the instance cannot be reached, or answers
`/api/schema/` with something that is not an OpenAPI document, the tool call
fails. It never quietly answers from the default bundled contract, because a
server that cannot describe the instance it is talking to should not pretend it
can. A failed attempt is not cached, so a transient outage does not disable the
server permanently.

Passing `--netbox-version` (or constructing `NetBoxMCPService(pinned_line=...)`
or `index=...`) makes that contract authoritative and skips detection entirely.

`dry_run` previews stay local and construct no client, so they are rendered from
the bundled contract and remain a *request preview* rather than server-side
validation.

## Install and run

```bash
pip install 'netbox-sdk[mcp]'
nbx-mcp
```

stdio is the default transport. For Streamable HTTP:

```bash
NETBOX_MCP_AUTH_TOKEN="$NETBOX_MCP_AUTH_TOKEN" nbx-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Pin the bundled release line with `--netbox-version` (alias `--api-version`) or
`NETBOX_SDK_NETBOX_VERSION`. Those are treated as operator instructions: an
unsupported value refuses to start rather than silently serving a different
line. The broader `NETBOX_API_VERSION` and `NETBOX_VERSION` variables are still
honoured when usable, but an unsupported value in them is ignored with a warning
— they are generic enough that a deployment may already set them for something
else. The pin is read **once, by the `nbx-mcp` entrypoint**, and handed to the
server; the server itself never re-reads process arguments or environment, so an
embedded host's own `--api-version` flag cannot repoint this server's schema.

Without a pin, `live=true` uses the shared SDK policy: a supported connected line
selects its bundle and an unsupported line fetches the live OpenAPI document.
Unlike `nbx`, a **detection or fetch failure is raised, not swallowed** — the
server must not silently answer from a bundled contract that does not describe
the instance it is talking to. Reading `/api/status/` is best-effort: if that
endpoint is blocked or malformed, detection falls back to the root
`API-Version` header.

The MCP endpoint is `/mcp`. Every Streamable HTTP bind requires a
shared-secret bearer token via `--auth-token` or `NETBOX_MCP_AUTH_TOKEN`; the
server raises `RuntimeError` and refuses to start without one, including on
loopback hosts (`127.0.0.1`, `localhost`, `::1`). Binding to loopback only
restricts *reachability* to this machine — it does not *authenticate* other
local processes or users, who could otherwise reach the server's loaded
NetBox credential (and any active `--allow-mutations` window) unauthenticated
on a shared dev or bastion host. Put TLS termination in front of it when it
is exposed beyond the local host — the bearer token authenticates the
caller, it does not encrypt the transport. Prefer `NETBOX_MCP_AUTH_TOKEN`
over `--auth-token` on any shared host: a CLI argument's value is visible to
other local users through `ps` and `/proc/<pid>/cmdline`, while the
environment variable is not.

This gate cannot be bypassed by calling the server object directly instead
of going through `run()`: `create_mcp_server()` always shadows the returned
server's `streamable_http_app` **and** `sse_app` with wrappers that enforce
the same `auth_token`, including raising `RuntimeError` when no token was
configured at all. There is no code path — `run("streamable-http")`,
`streamable_http_app()`, `run("sse")`, `sse_app()`, or otherwise — that
yields an unauthenticated network app from a `create_mcp_server()`-produced
instance. The `--transport` CLI flag only exposes `stdio` and
`streamable-http`, but any embedder holding the returned `FastMCP` instance
directly (not just the `nbx-mcp` entrypoint) could otherwise reach the SSE
transport unauthenticated, since it shares the same instance-attribute
shadowing mechanism as Streamable HTTP.

## Tool surface

| Tool | Behavior |
|---|---|
| `list_groups`, `list_resources`, `describe_operation` | Stable JSON schema introspection; `live=true` includes runtime resources |
| `list`, `get` | Schema-resolved reads; `list` supports pagination and repeated query keys; `live=true` dispatches against the same connected-instance schema `describe_operation(live=true)` reports, so a runtime-discovered resource can be listed or fetched, not just described |
| `filters` | Local filter introspection with no HTTP request |
| `create`, `update`, `patch`, `delete` | Detail mutations guarded off by default |
| `bulk_update`, `bulk_patch`, `bulk_delete` | List-path mutations guarded off by default |
| `plugin_discover` | Enrich the active schema through live plugin discovery |
| `plugin_list_tools` | Discover and validate semantic tools explicitly advertised by NetBox plugin API roots |
| `plugin_call_tool` | Invoke one advertised plugin operation through the configured SDK client; writes remain guarded off by default |
| `call` | Relative `/api/` escape hatch; GET/HEAD only while the mutation gate is closed |

Every tool input is validated by an explicit Pydantic schema. Names, IDs,
methods, relative API paths, list sizes, unknown fields, and credential control
characters are rejected before dispatch. Raw `call` paths containing an encoded
path separator (`%2F` or `%5C`, case-insensitive) are rejected before cache or
network access because routers disagree on whether those octets split segments.
Plugin manifests are also treated as hostile input: origin, namespace, path,
method/effect consistency, schemas, payloads, nesting, and sizes are checked
before target dispatch. See [NetBox Plugin Bridge](plugin-bridge.md) for the
wire contract and plugin-author checklist.

## Authentication

For stdio, the server loads the existing default profile from
`netbox_sdk.config`; it does not create a second credential store. Each tool
that contacts NetBox can instead receive a `token` bearer credential for that
call. Avoid placing tokens in logs, model-visible transcripts, or checked-in
server configuration.

This per-call NetBox token is separate from the Streamable HTTP transport's
own `--auth-token`/`NETBOX_MCP_AUTH_TOKEN` bearer gate described above: the
transport token authenticates *the MCP caller* to *this server*, while the
per-call `token` authenticates *this server* to *NetBox*.

## Mutation safety

Live writes are denied by default. Preview the request first with `dry_run=true`,
then start a deliberately scoped execution window with either:

```bash
NETBOX_MCP_ALLOW_MUTATIONS=1 nbx-mcp
nbx-mcp --allow-mutations
```

`dry_run=true` resolves the method, path, query, and body locally without
constructing a client. It is not server-side validation and does not prove that
the live NetBox call will succeed. The one exception is
`plugin_call_tool`: discovery of an advertised tool necessarily performs
read-only GET requests for the live plugin root and manifest. Its dry-run still
never dispatches the advertised target mutation.

The `nbx` process independently refuses dynamic CRUD/bulk writes, Proxbox
CRUD/sync or TUI launch, write-method raw/dev-HTTP calls, and mutating Branching
verbs unless the reviewed command includes `--confirm` or its environment
contains `NETBOX_SDK_CONFIRM_WRITE=1`.
Repository-local Claude Code and Codex hooks add a defense-in-depth early denial
for recognizable Bash source; decoded or generated shell input still reaches
the authoritative CLI-process gate.

## Agent operating sequence

1. Inspect `nbx capabilities --json`, or call `list_groups`, `list_resources`,
   `describe_operation`, and `plugin_list_tools`.
2. Preview every write with `--dry-run` or `dry_run=true`.
3. Explicitly enable/confirm only the reviewed operation and execute it.
4. Verify the result with `get` or a filtered `list`.

The repository ships this procedure as the mirrored
`netbox-sdk-operations` Skill under `.claude/skills/` and `.codex/skills/`.
