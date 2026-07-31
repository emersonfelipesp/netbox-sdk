# MCP Server

`netbox_mcp` provides a deliberately small Model Context Protocol surface over
the same `SchemaIndex`, request resolver, plugin discovery, pagination, client,
and profile configuration used by the SDK and CLI. It does not generate one
tool per OpenAPI operation, so its tool list stays stable when NetBox plugins
change the reachable resources.

## Install and run

```bash
pip install 'netbox-sdk[mcp]'
nbx-mcp
```

stdio is the default transport. For Streamable HTTP:

```bash
nbx-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

The MCP endpoint is `/mcp`. Binding to a non-loopback `--host` (anything other
than `127.0.0.1`, `localhost`, or `::1`) requires a shared-secret bearer token
via `--auth-token` or `NETBOX_MCP_AUTH_TOKEN`; the server raises `RuntimeError`
and refuses to start without one. Loopback binds may omit the token. Put TLS
termination in front of it when it is exposed beyond the local host — the
bearer token authenticates the caller, it does not encrypt the transport.

## Tool surface

| Tool | Behavior |
|---|---|
| `list_groups`, `list_resources`, `describe_operation` | Stable JSON schema introspection; `live=true` includes runtime resources |
| `list`, `get` | Schema-resolved reads; `list` supports pagination and repeated query keys |
| `filters` | Local filter introspection with no HTTP request |
| `create`, `update`, `patch`, `delete` | Detail mutations guarded off by default |
| `bulk_update`, `bulk_patch`, `bulk_delete` | List-path mutations guarded off by default |
| `plugin_discover` | Enrich the active schema through live plugin discovery |
| `call` | Relative `/api/` escape hatch; GET/HEAD only while the mutation gate is closed |

Every tool input is validated by an explicit Pydantic schema. Names, IDs,
methods, relative API paths, list sizes, unknown fields, and credential control
characters are rejected before dispatch.

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
the live NetBox call will succeed.

Repository-local Claude Code and Codex hooks apply an additional deterministic
gate to Bash-based CLI operations. They block `nbx` create, update, patch,
delete, and bulk writes unless the reviewed command is prefixed with
`NETBOX_SDK_CONFIRM_WRITE=1`.

## Agent operating sequence

1. Inspect `nbx capabilities --json`, or call `list_groups`, `list_resources`,
   and `describe_operation`.
2. Preview every write with `--dry-run` or `dry_run=true`.
3. Explicitly enable/confirm only the reviewed operation and execute it.
4. Verify the result with `get` or a filtered `list`.

The repository ships this procedure as the mirrored
`netbox-sdk-operations` Skill under `.claude/skills/` and `.codex/skills/`.
