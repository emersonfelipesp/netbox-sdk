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
