# Commands

All top-level `nbx` commands. Run any command with `--help` for the full option list.

---

## `nbx init`

Interactive setup for the default profile. Prompts for NetBox URL, token key, token secret, and timeout. Saves to `~/.config/netbox-cli/config.json`.

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

## `nbx tui`

Launch the interactive Textual TUI.

```bash
nbx tui
nbx tui --theme dracula
nbx tui --theme          # list available themes
```

**Options**

| Flag | Description |
|------|-------------|
| `--theme` | List themes (no argument) or launch with a specific theme name |

See [TUI Guide](../tui/index.md) for full navigation documentation.

---

## `nbx logs`

Launch the structured JSON log viewer TUI. Shows entries written to `~/.config/netbox-cli/logs/netbox-cli.log` by the CLI and TUI.

```bash
nbx logs
nbx logs --limit 500     # load up to 500 entries (default: 200)
nbx logs --theme dracula
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `--limit` | `200` | Maximum number of log entries to load |
| `--theme` | from saved state | Theme name to use |

Use `Ctrl+G` inside the log viewer to clear the log file.

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

## `nbx docs generate-capture`

Generate the command capture documentation — runs every `nbx` command, records output, and writes `docs/generated/nbx-command-capture.md` plus per-command JSON files.

```bash
nbx docs generate-capture
nbx docs generate-capture --live   # use default profile instead of demo
```

**Options**

| Flag | Default | Description |
|------|---------|-------------|
| `-o` / `--output` | `docs/generated/nbx-command-capture.md` | Markdown output path |
| `--raw-dir` | `docs/generated/raw/` | Directory for per-command JSON files |
| `--live` | off | Use default profile (real NetBox) instead of demo profile |

See [Documentation Generation](../developer/docgen.md) for the full guide.
