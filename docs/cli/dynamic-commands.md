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
nbx ipam prefixes create --body-json '{...}'
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
| `list` | `GET` | `/api/<group>/<resource>/` | Returns paginated list |
| `get` | `GET` | `/api/<group>/<resource>/{id}/` | Requires `--id` |
| `create` | `POST` | `/api/<group>/<resource>/` | Requires `--body-json` or `--body-file` |
| `update` | `PUT` | `/api/<group>/<resource>/{id}/` | Requires `--id` and body |
| `patch` | `PATCH` | `/api/<group>/<resource>/{id}/` | Requires `--id` and body |
| `delete` | `DELETE` | `/api/<group>/<resource>/{id}/` | Requires `--id` |

Not every resource supports all actions — availability depends on the OpenAPI schema.

---

## Options (all actions)

| Flag | Description |
|------|-------------|
| `--id INTEGER` | Object ID for detail operations (`get`, `update`, `patch`, `delete`) |
| `-q` / `--query KEY=VALUE` | Query string filter (repeatable) |
| `--body-json TEXT` | Inline JSON request body |
| `--body-file PATH` | Path to JSON file for request body |
| `--json` | Output raw JSON |
| `--yaml` | Output YAML |
| `--markdown` | Output table-first Markdown |
| `--trace` | Fetch and render ASCII cable trace (interfaces only, `get` only) |
| `--select TEXT` | JSON dot-path to extract specific field from response (e.g., `results.0.name`) |
| `--columns TEXT` | Comma-separated list of columns to display in table output |
| `--max-columns INTEGER` | Maximum number of columns to display (default: 6) |
| `--dry-run` | Preview write operation without executing (create/update/patch/delete only) |

`--json`, `--yaml`, and `--markdown` are mutually exclusive.

---

## Filtering

The `-q` / `--query` flag maps to NetBox API query parameters:

```bash
nbx dcim devices list -q site=nyc01
nbx dcim devices list -q status=active -q role=spine
nbx ipam prefixes list -q family=6 -q status=active
nbx dcim interfaces list -q device_id=1
```

Multiple `-q` flags are ANDed together.

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
```

Output shows the HTTP method, path, and request body in a formatted table. The `--dry-run` flag is only valid for write operations (`create`, `update`, `patch`, `delete`).

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

At startup, `_register_openapi_subcommands()` in `cli.py` reads `reference/openapi/netbox-openapi.json`, builds a `SchemaIndex`, then creates a Typer sub-app for every group, a nested sub-app for every resource, and a command for every supported action. The same registration runs twice — once for the root `app` and once for `demo_app` with `_get_demo_client` as the client factory.

For plugin/custom-object resources, the bundled schema gives `nbx` the static command tree it knows about. Use `--live` with `groups`, `resources`, or `ops` to enrich that index from the configured NetBox instance via `/api/plugins/` and `/api/core/object-types/`. Free-form dynamic invocations also try live enrichment when the requested resource is missing from the bundled schema.
