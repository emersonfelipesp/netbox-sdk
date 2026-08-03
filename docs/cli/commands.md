# Commands

All top-level `nbx` commands. Run any command with `--help` for the full option list.

---

## `nbx init`

Interactive setup for the default profile. Prompts for NetBox URL, token key,
token secret, and timeout. Saves to `~/.config/netbox-sdk/config.json`.

Older `~/.config/netbox-cli/config.json` files are still read automatically if a
new NetBox SDK config has not been written yet.

```bash
nbx init
```

Any command that needs a connection will also trigger this prompt automatically if config is missing.

---

## `nbx config`

Display the current default profile configuration.

```bash
nbx config
nbx config --show-token   # reveal token key and secret
```

**Options**

| Flag | Description |
|------|-------------|
| `--show-token` | Include token key and secret in output (plaintext) |

---

## `nbx test`

Test connectivity to your configured NetBox instance (default profile). Also
checks whether a Django model graph build exists for the detected NetBox
version, which is used by `nbx dev django-model`.

```bash
nbx test
nbx test --fetch    # clone and build from GitHub if no matching build found
```

**Options**

| Flag | Description |
|------|-------------|
| `--fetch` / `-f` | If no matching Django model build exists for the detected version, clone it from GitHub and build it automatically |

---

## `nbx groups`

List all OpenAPI app groups available in the bundled schema.

```bash
nbx groups
```

Output is one group name per line: `circuits`, `core`, `dcim`, `extras`, `ipam`, `plugins`, `tenancy`, `users`, `virtualization`, `vpn`, `wireless`.

---

## `nbx resources GROUP`

List all resources within an app group.

```bash
nbx resources dcim
nbx resources ipam
```

---

## `nbx ops GROUP RESOURCE`

Show all HTTP operations (method, path, operation ID) for a specific resource.

```bash
nbx ops dcim devices
nbx ops ipam prefixes
```

Output is a Rich table with columns: **Method**, **Path**, **Operation ID**.

---

## `nbx call METHOD PATH`

Make an explicit HTTP request to any NetBox API path.

```bash
nbx call GET /api/status/
nbx call GET /api/dcim/sites/ --json
nbx call GET /api/dcim/sites/ --markdown
nbx call POST /api/ipam/ip-addresses/ --body-json '{"address":"192.0.2.1/24","status":"active"}' --confirm
nbx call PUT /api/dcim/devices/1/ --body-file ./device.json --confirm
```

**Options**

| Flag | Description |
|------|-------------|
| `-q` / `--query KEY=VALUE` | Query string parameter (repeatable) |
| `--body-json TEXT` | Inline JSON request body |
| `--body-file PATH` | Path to a JSON file to use as request body |
| `--json` | Output raw JSON instead of a Rich table |
| `--yaml` | Output as YAML |
| `--markdown` | Output API responses as table-first Markdown |
| `--confirm` | Confirm a `POST`, `PUT`, `PATCH`, or `DELETE` request |

`--json`, `--yaml`, and `--markdown` are mutually exclusive.
Write methods are refused unless `--confirm` is passed or
`NETBOX_SDK_CONFIRM_WRITE=1` is present in the `nbx` process environment.

---

## `nbx proxbox resources`

List the dedicated `netbox-proxbox` catalog as a Rich-colored table or JSON.
The catalog includes command paths, categories, supported actions, API paths,
and read-only status.

```bash
nbx proxbox resources
nbx proxbox resources --json
```

---

## `nbx proxbox ops RESOURCE`

Show HTTP operations for one Proxbox resource. `RESOURCE` can be a catalog key
such as `firewall/rules`, a command path such as
`operations/deletion-requests`, or the plugin resource name.

```bash
nbx proxbox ops firewall/rules
nbx proxbox ops operations/deletion-requests --json
```

---

## `nbx proxbox <family> <resource> ACTION`

Run catalog-backed Proxbox CRUD commands. Writable model resources expose
`list`, `get`, `create`, `update`, `patch`, and `delete`; read-only resources
only register read actions. Write actions support `--dry-run` previews.

```bash
nbx proxbox endpoints proxmox list -q name=pve-prod
nbx proxbox endpoints proxmox create --body-json '{"name":"pve-prod"}' --confirm
nbx proxbox firewall rules patch --id 7 --body-json '{"enabled":false}' --confirm
nbx proxbox operations deletion-requests get --id 12
nbx proxbox firewall rules patch --id 7 --dry-run --body-json '{"enabled":false}'
```

See [Proxbox](proxbox.md) for the resource families and full workflow examples.

---

## `nbx proxbox tui`

Launch the Proxbox-focused Textual request workbench. It uses the same request
editor and response panes as `nbx dev tui`, but starts from the stable Proxbox
catalog and disables live plugin discovery.

```bash
nbx proxbox tui
nbx proxbox tui --theme dracula
nbx proxbox tui --theme
```

---

## `nbx proxbox sync [ENDPOINT]`

Trigger a synchronization job through the `netbox-proxbox` plugin and stream
Server-Sent Events until the job reports completion. `ENDPOINT` is optional; it
can be a Proxmox endpoint primary key or exact endpoint name. Omit it to sync
all configured Proxmox endpoints.

```bash
nbx proxbox sync --confirm
nbx proxbox sync pve-prod -t virtual-machines -t storage --confirm
nbx proxbox sync 12 -t all --job-name nightly-proxbox-sync --confirm
nbx proxbox sync --json --confirm
```

The live view shows the scheduled job, per-phase progress bars, recent stream
events, and an authoritative final summary. After the stream ends, the CLI
fetches `/api/core/jobs/{job_id}/` and merges job errors and error-level log
entries with streamed errors so throttled server-side SSE messages are not lost.
If the SSE stream times out, disconnects, or fails protocol validation after
scheduling, the CLI still fetches that job and reports its `job_id`,
authoritative status, and the stream error to prevent an unsafe duplicate sync.

**Options**

| Flag | Description |
|------|-------------|
| `-t` / `--type TEXT` | Proxbox sync type slug. Repeat for multiple types. Defaults to `all` |
| `--job-name TEXT` | Optional NetBox job name |
| `--timeout FLOAT` | Maximum seconds to keep the SSE stream open (default: `7200`) |
| `--json` | Skip the live UI and emit `{job_id,status,ok,errors,summary}` JSON |
| `--confirm` | Confirm scheduling the live synchronization job |

Valid sync types are: `virtual-machines`, `storage`, `vm-disks`, `vm-backups`,
`vm-snapshots`, `devices`, `network-interfaces`, `vm-interfaces`,
`ip-addresses`, `sdn`, `backup-routines`, `replications`, `task-history`, and
`all`. The `all` type cannot be combined with any other type.

---

## `nbx proxbox sync-types`

Print the sync type slugs accepted by `nbx proxbox sync`.

```bash
nbx proxbox sync-types
```

---

## `nbx graphql QUERY`

Execute a GraphQL query against the NetBox API.

```bash
# Simple query
nbx graphql "{ sites { name } }"

# Query with variables
nbx graphql "query($id: Int!) { device(id: $id) { name } }" --variables '{"id": 1}'

# Query with key=value variables
nbx graphql "query($name: String!) { devices(name: $name) { id } }" --variables name=sw01

# Multiple variables (repeat -v / --variables)
nbx graphql "query($a: Int!, $b: Int!) { __typename }" -v a=1 -v b=2

# Output as JSON
nbx graphql "{ sites { name } }" --json
```

**Options**

| Flag | Description |
|------|-------------|
| `--variables` / `-v TEXT` | GraphQL variables: one JSON object, or repeat for multiple `key=value` pairs |
| `--json` | Output raw JSON instead of formatted table |
| `--yaml` | Output as YAML |

See [GraphQL](graphql.md) for focused examples and guidance.

---

## `nbx graphql tui`

Launch the dedicated interactive GraphQL explorer and query runner.

```bash
nbx graphql tui
nbx graphql tui --theme dracula
nbx graphql tui --theme

nbx demo graphql tui
nbx demo graphql tui --theme dracula
```

This TUI loads GraphQL schema introspection from the current NetBox instance,
lets you browse root fields and their arguments, inserts query/filter/pagination
skeletons into an editor, and executes arbitrary GraphQL queries with optional
JSON variables.

**Options**

| Flag | Description |
|------|-------------|
| `--theme` | List themes (no argument) or launch with a specific theme name |

See [GraphQL](graphql.md) and [GraphQL TUI](../tui/graphql.md) for the full workflow.

---

## `nbx tui`

Launch the main interactive Textual browser.

```bash
nbx tui
nbx tui --theme dracula
nbx tui --theme          # list available themes
```

**Options**

| Flag | Description |
|------|-------------|
| `--theme` | List themes (no argument) or launch with a specific theme name |

See [TUI Guide](../tui/index.md) for the main browser workflow.

---

## `nbx logs`

Print recent structured application logs from the shared log file.

```bash
nbx logs
nbx logs --limit 500     # load up to 500 entries (default: 200)
nbx logs --source
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | `200` | Maximum number of log entries to load |
| `--source` | off | Include module/function/line details |

New installs write logs under `~/.config/netbox-sdk/logs/netbox-sdk.log`, with
compatibility reads from older `netbox-cli` log files when present.

For the full-screen Textual log viewer, use `nbx tui logs`.

---

## `nbx dev tui`

Launch the developer request workbench TUI against your default profile.

```bash
nbx dev tui
nbx dev tui --theme dracula
nbx dev tui --theme          # list available themes
```

This view is designed for API exploration and request crafting rather than the standard browse/results workflow.
When you launch the same view through `nbx demo dev tui`, the CLI automatically refreshes expired demo v1 tokens if demo credentials were saved during `nbx demo init`.

**Options**

| Flag | Description |
|------|-------------|
| `--theme` | List themes (no argument) or launch with a specific theme name |

---

## `nbx dev http`

Developer-oriented HTTP helpers for exploring arbitrary API paths and operations.

```bash
nbx dev http paths
nbx dev http ops --path /api/dcim/devices/
nbx dev http get --path /api/status/
```

Use `nbx dev http --help` and the subcommand helps for the full option matrix.

---

## `nbx cli tui`

Launch the guided command-builder TUI.

```bash
nbx cli tui
nbx demo cli tui
```

This is useful when you want to explore the command tree visually and execute an
assembled `nbx` command without leaving the terminal.

---

## `nbx dev django-model`

Contributor-oriented helpers for parsing, caching, fetching, and browsing
NetBox's internal Django models.

```bash
nbx dev django-model build
nbx dev django-model fetch --auto
nbx dev django-model tui
```

---

## `nbx docs generate-capture`

Generate the docs-safe command-capture artifacts used by the MkDocs reference pages.
Docgen only targets the demo profile and should never run against production.

```bash
nbx docs generate-capture
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/nbx-command-capture.md` | Markdown output path |
| `--raw-dir` | `docs/generated/raw/` | Directory for per-command JSON files |
| `--markdown` | on | Append `--markdown` to compatible captures |
| `-j` / `--concurrency` | `4` | Parallel capture worker count |

See [Documentation Generation](../developer/docgen.md) for the full guide.

---

## `nbx docs generate-tui-simulation`

Generate fixture-backed SVG screenshots of the main NetBox TUI browser in
multiple themes and states. The output is used by the website and docs pages
that embed interactive-style TUI previews.

```bash
nbx docs generate-tui-simulation
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/tui-simulation/main-browser.json` | Manifest JSON destination |
| `--assets-dir` | Parent directory of `--output` | SVG destination directory |

The command writes one manifest JSON file and one SVG file per
`(theme × state)` combination to `docs/generated/tui-simulation/`. The themes
and states rendered are defined in `netbox_cli/tui_simulation.py`. Unlike
`generate-capture`, this command uses fixture data and does not require a live
NetBox instance or demo credentials.

See [Documentation Generation](../developer/docgen.md) for the full pipeline.
