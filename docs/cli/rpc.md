# RPC

`nbx rpc` is the maintained command surface for the officially supported
`netbox-rpc` plugin. It combines policy-correct standard REST operations with
workflow commands that generic OpenAPI discovery cannot infer.

## Collection contract

| Collection | Standard commands | Workflow commands |
|---|---|---|
| `settings` | `list`, `get`, `patch` | — |
| `backends` | list/get/create/update/patch/delete and all three bulk writes | — |
| `procedures` | list/get/create/update/patch/delete and all three bulk writes | `available`, `commands` |
| `procedure-commands` | list/get/create/update/patch/delete and all three bulk writes | — |
| `intents` | list/get/create/update/patch/delete and all three bulk writes | `run` |
| `linux-service-allowlist` | list/get/create/update/patch/delete and all three bulk writes | — |
| `netbox-plugin-allowlist` | list/get/create/update/patch/delete and all three bulk writes | — |
| `executions` | `list`, `get`, `create` | `cancel`, `approve`, `reject`, `events`, `wait` |
| `execution-events` | `list`, `get` | — |

The bulk commands are `bulk-update` (`PUT`), `bulk-patch` (`PATCH`), and
`bulk-delete` (`DELETE`). They accept a JSON array and always target the
collection path. Standard NetBox collection POST also accepts an array, so the
ordinary `create` command is both the single-record and bulk-create command.

## Procedures and commands

```bash
nbx rpc procedures create \
  --body-json '{"name":"service-status","handler_id":"linux.service.status","version":"1.0","enabled":true,"target_models":["dcim.device"],"effect":"read","timeout_seconds":30,"approval_required":false,"params_schema":{"type":"object"}}' \
  --confirm --json
nbx rpc procedures get --id 6 --json
nbx rpc procedures patch --id 6 \
  --body-json '{"description":"Read one systemd service state"}' \
  --confirm --json
nbx rpc procedures available --target-type dcim.device -q limit=100 --json
nbx rpc procedures commands --id 6 -q limit=100 --json
nbx rpc procedures commands --id 6 \
  --body-json '{"argv":["systemctl","status","nginx"]}' --confirm --json
nbx rpc procedures delete --id 6 --confirm --json
```

Supplying `--body-json` or `--body-file` to `procedures commands` changes the
request from GET to POST and therefore requires `--confirm`. `-q` / `--query`
is repeatable on the read form and preserves repeated keys; a command-creation
POST rejects query options instead of silently dropping them. Procedure
commands can also be fully managed through the standalone
`procedure-commands` collection.

## Intents and executions

```bash
nbx rpc intents create \
  --body-json '{"name":"inspect-service","execution_mode":"sequential","enabled":true,"procedure_ids":[6]}' \
  --confirm --json
nbx rpc intents get --id 2 --json
nbx rpc intents update --id 2 \
  --body-json '{"name":"inspect-service","execution_mode":"parallel","enabled":true,"procedure_ids":[6,7]}' \
  --confirm --json
nbx rpc intents patch --id 2 --body-json '{"enabled":false}' --confirm --json
nbx rpc intents run --id 2 \
  --assigned-object-type dcim.device --assigned-object-id 42 \
  --params-json '{"service_slug":"nginx"}' --confirm --json

nbx rpc executions create \
  --body-json '{"procedure_id":6,"assigned_object_type":"dcim.device","assigned_object_id":42,"params":{}}' \
  --confirm --json
nbx rpc executions approve --id 100 --reason reviewed --confirm --json
nbx rpc executions reject --id 101 --reason unsafe --confirm --json
nbx rpc executions cancel --id 102 --confirm --json
nbx rpc executions events --id 100 -q limit=100 --json
```

`--params-file` and `--body-file` are the file-based alternatives to inline
JSON. NetBox remains authoritative for JSON Schema admission, target
restrictions, permissions, and approval policy.

Every custom POST and every standard write confirms before the HTTP client is
constructed. Standard CRUD commands also support the shared client-free,
recursively redacted `--dry-run` preview.

Use the same standard commands for `backends`, `procedure-commands`,
`linux-service-allowlist`, and `netbox-plugin-allowlist`. The latter manages
the server-controlled distributions, modules, paths, and services that RPC
plugin-install procedures may use; the server remains authoritative for
validation and permissions. The server intentionally
restricts `settings` to list/get/patch, `executions` to list/get/create, and
`execution-events` to list/get; `nbx rpc` does not advertise unsupported
mutations.

## Bounded waiting

```bash
nbx rpc executions wait --id 100 --timeout 300 --interval 2 --json
```

Both bounds must be finite and greater than zero. Waiting stops on `succeeded`,
`failed`, `cancelled`, `rejected`, or `expired`; `approved` is not terminal. An
HTTP error response returns immediately. A nonterminal or malformed successful
response is polled until the deadline and then raises a timeout error.
Every poll bypasses the normal response cache so state transitions are observed
at the requested interval.

## Automation rules

- Prefer `--json` for scripts.
- Use file-based payloads when shell history must not contain parameters.
- Never retry a mutation merely because response rendering failed; inspect the
  execution first.
- Generic `nbx plugins ...` discovery remains suitable for standard third-party
  plugin CRUD, but cannot replace the explicit RPC workflow commands.
