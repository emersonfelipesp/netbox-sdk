---
name: netbox-sdk-operations
description: Safely inspect and operate NetBox through the netbox-sdk CLI or MCP server. Use for NetBox discovery, reads, creates, updates, patches, deletes, bulk writes, raw API calls, plugin resources, and any workflow that must preview and verify changes deterministically.
---

# NetBox SDK Operations

Follow this sequence for every NetBox task.

## 1. Introspect first

Discover the reachable schema before choosing an operation:

```bash
nbx capabilities --json
nbx groups --json
nbx resources dcim --json
nbx ops dcim devices --json
```

For MCP, call `list_groups`, `list_resources`, then `describe_operation`. Use
`live=true` or `plugin_discover` when installed plugin resources may not be in
the bundled schema.

## 2. Preview every write

Run the exact create, update, patch, delete, or bulk operation with `--dry-run`
or `dry_run=true`. Inspect the resolved method, path, query, and body.

A dry-run is only a local request preview. It does not contact NetBox, perform
server-side validation, or prove that the live write will succeed.

## 3. Execute deliberately

Confirm the target instance, group, resource, object IDs, and payload. Enable MCP
mutations only for the execution window with `NETBOX_MCP_ALLOW_MUTATIONS=1` or
`nbx-mcp --allow-mutations`.

For CLI writes run through agent Bash tools, prefix the reviewed invocation with:

```bash
NETBOX_SDK_CONFIRM_WRITE=1 nbx <group> <resource> <write-action> ...
```

Never place credentials in commands, output, or logs. Use the existing
`netbox_sdk.config` profile store or the MCP tool's per-call bearer-token field.

## 4. Verify the resulting state

After a successful write, call `get` for affected IDs or repeat a filtered
`list`. Compare the live result with the intended payload and report any
server-side normalization or partial failure.

## Failure handling

| Failure | Required response |
|---|---|
| Resource not found in schema | Retry live introspection, call MCP `plugin_discover`, or inspect `nbx plugins ...`; do not guess a path. |
| Mutation denied | Explain that writes are disabled by default and name the explicit MCP opt-in or CLI confirmation marker. Do not bypass the gate implicitly. |
| Dry-run succeeds but live call fails | Explain that dry-run is a local preview only. Report the live HTTP error and correct the payload, permissions, concurrency header, or resource selection before retrying. |
| Live write returns success but verification differs | Stop further writes, preserve the response, and report the observed state before proposing another change. |
