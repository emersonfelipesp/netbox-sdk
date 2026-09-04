# Dynamic Commands

Every NetBox resource reachable through the API is automatically registered as a Typer subcommand, derived from the bundled OpenAPI schema at import time. This means `--help` works at every level and shell completion is fully supported.

---

## Command structure

```
nbx <group> <resource> <action> [options]
```

For example:

```bash
nbx dcim devices list
nbx dcim devices get --id 1
nbx ipam prefixes create --body-json '{...}' --confirm
```

---

## Discovery

Use the discovery commands to explore what's available:

```bash
# All app groups
nbx groups
# → circuits, core, dcim, extras, ipam, plugins, tenancy, users, virtualization, vpn, wireless

# Resources in a group
nbx resources dcim
# → cable-terminations, cables, console-ports, device-bays, device-roles, devices, …

# Include plugin/custom-object resources from the configured NetBox instance
nbx resources plugins --live

# Help at any level
nbx dcim --help
nbx dcim devices --help
nbx dcim devices list --help
```

---

## Actions

| Action | HTTP method | Path | Notes |
|--------|------------|------|-------|
| `list` | `GET` | `/api/<group>/<resource>/` | Returns paginated list; supports `--all` |
| `get` | `GET` | `/api/<group>/<resource>/{id}/` | Requires `--id` |
| `create` | `POST` | `/api/<group>/<resource>/` | Requires `--body-json` or `--body-file` |
| `update` | `PUT` | `/api/<group>/<resource>/{id}/` | Requires `--id` and body |
| `patch` | `PATCH` | `/api/<group>/<resource>/{id}/` | Requires `--id` and body |
| `delete` | `DELETE` | `/api/<group>/<resource>/{id}/` | Requires `--id` |
| `bulk-update` | `PUT` | `/api/<group>/<resource>/` | Array body; no `--id`; list path |
| `bulk-patch` | `PATCH` | `/api/<group>/<resource>/` | Array body; no `--id`; list path |
| `bulk-delete` | `DELETE` | `/api/<group>/<resource>/` | Array body; no `--id`; list path |
| `filters` | — | local only | Prints available filter parameters from schema |

Not every resource supports all actions — availability depends on the OpenAPI schema.

---

## Options (all actions)

| Flag | Description |
|------|-------------|
| `--netbox-version` / `--api-version` | Global option to force a supported bundled schema release line (`4.3`, `4.4`, `4.5`, `4.6`, `4.7`) |
| `--id INTEGER` | Object ID for detail operations (`get`, `update`, `patch`, `delete`) |
| `-q` / `--query KEY=VALUE` | Query string filter (repeatable) |
| `-H` / `--header HEADER=VALUE` | HTTP header for the request; `Header: Value` is also accepted (repeatable) |
| `--body-json TEXT` | Inline JSON request body |
| `--body-file PATH` | Path to JSON file for request body |
| `--all` | Auto-paginate: follow `next` links and return all records (`list` only) |
| `--max-records INTEGER` | Upper bound for `--all` (default: 10 000) |
| `--json` | Output raw JSON |
| `--yaml` | Output YAML |
| `--markdown` | Output table-first Markdown |
| `--trace` | Fetch and render ASCII cable trace (interfaces only, `get` only) |
| `--select TEXT` | JSON dot-path to extract specific field from response (e.g., `results.0.name`) |
| `--columns TEXT` | Comma-separated list of columns to display in table output |
| `--max-columns INTEGER` | Maximum number of columns to display (default: 6) |
| `--dry-run` | Preview a create/update/patch/delete/bulk write without executing |
| `--confirm` | Confirm execution of a live create/update/patch/delete/bulk write |

`--json`, `--yaml`, and `--markdown` are mutually exclusive.

---

## NetBox version selection

`nbx` supports every bundled NetBox command surface in parallel (`4.3`, `4.4`, `4.5`, `4.6`, and `4.7`):

- By default, the static command tree uses the official bundled NetBox 4.7 GA schema.
- During command execution, discovery helpers, and TUI launch, `nbx` checks the configured instance version and uses the matching bundled schema for supported release lines.
- If a configured instance cannot be reached, version detection fails, or its live schema is invalid, execution fails closed instead of substituting the default bundled contract.
- Client-free `--dry-run` previews use the explicit/static schema that registered the command and never probe the instance.
- Use `--netbox-version` / `--api-version` or `NETBOX_SDK_NETBOX_VERSION` to pin the bundled schema explicitly.

```bash
# Default 4.7 command discovery
nbx dcim cable-bundles list --help

# Pin command discovery and execution to NetBox 4.5
nbx --netbox-version 4.5 dcim devices list
NETBOX_SDK_NETBOX_VERSION=4.5 nbx resources dcim
```

Patch versions normalize to their release line: `4.5.10` uses `4.5`, and `4.6.2` uses `4.6`.

---

## Filtering

The `-q` / `--query` flag maps to NetBox API query parameters:

```bash
nbx dcim devices list -q site=nyc01
nbx dcim devices list -q status=active -q role=spine
nbx ipam prefixes list -q family=6 -q status=active
nbx dcim interfaces list -q device_id=1
nbx extras tags list -q tag=prod -q tag=edge
```

Multiple `-q` flags are ANDed together. Repeating the same key preserves repeated query parameters, which NetBox uses for filters such as multiple tags.

---

## HTTP headers

Use `-H` / `--header` on dynamic commands, `nbx call`, and `nbx dev http` when the API interaction needs conditional headers such as `If-Match` or custom headers:

```bash
nbx dcim devices patch --id 42 -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx call PATCH /api/dcim/devices/42/ -H 'If-Match: "etag-value"' --body-json '{"status":"active"}' --confirm
nbx dev http get --path /api/dcim/devices/ -H 'Accept: application/json'
```

---

## Filter discovery (`filters`)

The `filters` action prints the available query parameters for a resource directly from the bundled schema — no HTTP request is made:

```bash
nbx dcim devices filters
nbx extras tags filters
nbx ipam prefixes filters
```

Example output for `extras tags`:

```
Filter parameters for extras/tags:

  q          (string)  — Search
  color      (string)
  id         (integer)
  name       (string)
  slug       (string)
```

Use this to discover what `-q` keys are valid before running a filtered `list`.

---

## Auto-pagination (`--all`)

By default, `list` returns one page (up to the NetBox server page size, typically 50 records). Use `--all` to follow every `next` link and receive a single synthesised response containing all matching records:

```bash
# Fetch all devices regardless of page size
nbx dcim devices list --all

# Cap at 200 records across all pages
nbx dcim devices list --all --max-records 200

# Combine with filters
nbx dcim devices list --all -q status=active --json
```

`--max-records` defaults to 10 000. When the accumulated count reaches the cap, pagination stops and the partial result is returned.
Repeated page targets, malformed `results` values, and pages that provide a
further `next` link without adding records fail with `PaginationError` instead
of retrying indefinitely.

---

## Bulk operations

Bulk operations target the list path with an array body — no `--id` is needed or accepted.

```bash
# Bulk-patch: partial update for multiple objects
nbx extras tags bulk-patch --body-json '[{"id":1,"color":"aa1409"},{"id":2,"color":"0c7a00"}]' --confirm

# Bulk-update: full replacement for multiple objects (all required fields must be present)
nbx extras tags bulk-update --body-json '[{"id":1,"name":"tag-a","slug":"tag-a","color":"ff0000"}]' --confirm

# Bulk-delete: delete multiple objects by id
nbx extras tags bulk-delete --body-json '[{"id":1},{"id":2}]' --confirm
```

These actions are only registered for resources where the OpenAPI schema exposes PUT/PATCH/DELETE on the list path.

---

## Output formats

=== "Rich table (default)"

    ```bash
    nbx dcim devices list
    ```

    Renders a Rich table with prioritized columns: `id`, `name`, `status`, `site`, `role`, `type`, etc.

=== "JSON"

    ```bash
    nbx dcim devices list --json
    ```

    Prints the raw paginated API response as indented JSON. Useful for piping to `jq`.

=== "YAML"

    ```bash
    nbx dcim devices list --yaml
    ```

    Renders the response as YAML.

=== "Markdown"

    ```bash
    nbx dcim devices list --markdown
    ```

    Renders API JSON as table-first Markdown output.

---

## Field selection (`--select`)

Extract specific fields from the JSON response using dot notation:

```bash
# Get the first device's name
nbx dcim devices list --select results.0.name
```

Only numeric list indices are supported in paths (no wildcards such as `[*]`).

Supported path patterns:
- `results.0.name` — Access nested object at a numeric index
- `count` — Access top-level fields

---

## Column control (`--columns`, `--max-columns`)

Limit which columns appear in table output:

```bash
# Display only specific columns
nbx dcim devices list --columns id,name,status

# Limit total columns to 3
nbx dcim devices list --max-columns 3

# Combine both
nbx dcim devices list --columns id,name,status --max-columns 2
```

The `--columns` flag accepts a comma-separated list of field names to display. The `--max-columns` flag limits the total number of columns shown, defaulting to 6.

---

## Dry run (`--dry-run`)

Preview what a write operation would send without actually executing it:

```bash
# Preview a create operation
nbx dcim devices create --dry-run --body-json '{"name":"test-device","site":1}'

# Preview an update operation
nbx dcim devices update --dry-run --id 1 --body-json '{"name":"updated-name"}'

# Preview a delete operation
nbx dcim devices delete --dry-run --id 1

# Preview an explicit plugin request when the route is not in the bundled schema
nbx call POST /api/plugins/custom/widgets/ --dry-run --body-json '{"name":"widget-a"}'
```

Output shows the HTTP method, path, and request body in a formatted table. Raw
`nbx call` previews also show parsed query parameters and non-sensitive headers.
The `--dry-run` flag is only valid for actions that resolve to `POST`, `PUT`,
`PATCH`, or `DELETE` (including the named CRUD/bulk actions and write-method
`nbx call` requests).

Live writes are refused by the executing CLI unless the command includes
`--confirm` or the process environment contains
`NETBOX_SDK_CONFIRM_WRITE=1`. This gate applies to every dynamic action that
resolves to `POST`, `PUT`, `PATCH`, or `DELETE`, including a raw HTTP-method
action spelling, plus Proxbox CRUD/sync, write-method `nbx call` and
`nbx dev http` requests, and mutating `nbx branching`/`nbx branch` verbs,
regardless of whether `nbx` was launched directly, through a script, or from
a subprocess.
`--dry-run` does not require confirmation because it makes no HTTP request.

---

## Cable trace

For `dcim/interfaces`, the `get` action supports `--trace` to fetch and display the cable path as an ASCII diagram:

```bash
nbx dcim interfaces get --id 4 --trace
```

Output:

```
Cable Trace:
┌────────────────────────────────────┐
│         dmi01-akron-rtr01          │
│       GigabitEthernet0/1/1         │
└────────────────────────────────────┘
                │
                │  Cable #36
                │  Connected
                │
┌────────────────────────────────────┐
│       GigabitEthernet1/0/2         │
│         dmi01-akron-sw01           │
└────────────────────────────────────┘

Trace Completed - 1 segment(s)
```

---

## Demo profile variant

The same dynamic command tree is registered under `nbx demo` and targets `demo.netbox.dev`:

```bash
nbx demo dcim devices list
nbx demo ipam prefixes list
nbx demo dcim interfaces get --id 4 --trace
```

See [Demo Profile](demo-profile.md) for setup.

---

## How it works

At startup, `_register_openapi_subcommands()` in `dynamic.py` builds a network-free `SchemaIndex` from the bundled schema selected by `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION`, defaulting to NetBox 4.7. It then creates a Typer sub-app for every group, a nested sub-app for every resource, and a command for every supported action. The same registration runs twice — once for the root `app` and once for `demo_app` with the demo client factory.

Actual command execution uses `_get_runtime_index()` from `runtime.py`. Explicit version overrides win; otherwise the CLI probes the configured instance and selects the matching bundled schema for supported NetBox release lines. A configured profile's detection or schema failure is terminal; only profiles without a base URL may use the default bundled contract. Dry-run previews remain network-free and resolve against the static registration index.

For plugin/custom-object resources, the bundled schema gives `nbx` the static command tree it knows about. Use `--live` with `groups`, `resources`, or `ops` to enrich that index from the configured NetBox instance via `/api/plugins/` and `/api/core/object-types/`. Free-form dynamic invocations also try live enrichment when the requested resource is missing from the bundled schema.
