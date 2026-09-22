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
| `executions` | `list`, `get`, `create` | `cancel`, `approve`, `reject`, `events`, `wait` |
| `execution-events` | `list`, `get` | — |

The bulk commands are `bulk-update` (`PUT`), `bulk-patch` (`PATCH`), and
`bulk-delete` (`DELETE`). They accept a JSON array and always target the
collection path.

## Procedures and commands

```bash
nbx rpc procedures available --target-type dcim.device --json
nbx rpc procedures commands --id 6 --json
nbx rpc procedures commands --id 6 \
  --body-json '{"argv":["systemctl","status","nginx"]}' --confirm --json
```

Supplying `--body-json` or `--body-file` to `procedures commands` changes the
request from GET to POST and therefore requires `--confirm`.

## Intents and executions

```bash
nbx rpc intents run --id 2 \
  --assigned-object-type dcim.device --assigned-object-id 42 \
  --params-json '{"service_slug":"nginx"}' --confirm --json

nbx rpc executions create \
  --body-json '{"procedure_id":6,"assigned_object_type":"dcim.device","assigned_object_id":42,"params":{}}' \
  --confirm --json
nbx rpc executions approve --id 100 --reason reviewed --confirm --json
nbx rpc executions reject --id 101 --reason unsafe --confirm --json
nbx rpc executions cancel --id 102 --confirm --json
nbx rpc executions events --id 100 --json
```

`--params-file` and `--body-file` are the file-based alternatives to inline
JSON. NetBox remains authoritative for JSON Schema admission, target
restrictions, permissions, and approval policy.

Every custom POST and every standard write confirms before the HTTP client is
constructed. Standard CRUD commands also support the shared client-free,
recursively redacted `--dry-run` preview.

## Bounded waiting

```bash
nbx rpc executions wait --id 100 --timeout 300 --interval 2 --json
```

Both bounds must be finite and greater than zero. Waiting stops on `succeeded`,
`failed`, `cancelled`, `rejected`, or `expired`; `approved` is not terminal. An
HTTP error response returns immediately. A nonterminal or malformed successful
response is polled until the deadline and then raises a timeout error.

## Automation rules

- Prefer `--json` for scripts.
- Use file-based payloads when shell history must not contain parameters.
- Never retry a mutation merely because response rendering failed; inspect the
  execution first.
- Generic `nbx plugins ...` discovery remains suitable for standard third-party
  plugin CRUD, but cannot replace the explicit RPC workflow commands.
