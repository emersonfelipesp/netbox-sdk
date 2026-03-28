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
nbx call POST /api/ipam/ip-addresses/ --body-json '{"address":"192.0.2.1/24","status":"active"}'
nbx call PUT /api/dcim/devices/1/ --body-file ./device.json
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

`--json`, `--yaml`, and `--markdown` are mutually exclusive.

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
