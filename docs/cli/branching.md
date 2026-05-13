# Branching

The CLI exposes a Typer subapp for every operation on the
[`netbox-branching`](https://github.com/netboxlabs/netbox-branching) plugin.

```bash
nbx branching --help
nbx branch --help   # alias
```

## Status & listing

```bash
nbx branching status
nbx branching list [--status ready]
nbx branching show <id-or-schema_id>
nbx branching models    # branchable model registry
nbx branching events
nbx branching changes [--branch <schema_id>]
```

## Lifecycle

```bash
nbx branching create --name feature-x [--description ...]
nbx branching update <id|schema_id> [--name ...]
nbx branching delete <id|schema_id> [--yes]
nbx branching archive <id|schema_id>
```

## Actions

`sync`, `merge`, and `revert` return queued jobs. `--wait` polls until the
job finishes.

```bash
nbx branching sync   <id|schema_id> [--wait] [--acknowledge-conflicts]
nbx branching merge  <id|schema_id> [--wait] [--acknowledge-conflicts]
nbx branching revert <id|schema_id> [--wait]
```

If the server returns a conflict body, the CLI prints a structured table and
exits with a non-zero status.

## Branch-scoped requests

A global `--branch` option (also reads the `NETBOX_BRANCH` env variable)
wraps the current invocation so **every** command — DCIM, IPAM, dynamic
OpenAPI commands, etc. — sends the `X-NetBox-Branch` header for the lifetime
of the call:

```bash
nbx --branch feature-x dcim devices list
NETBOX_BRANCH=feature-x nbx ipam prefixes list
```

The argument resolves either a `schema_id` or a branch name to the underlying
`schema_id`.
