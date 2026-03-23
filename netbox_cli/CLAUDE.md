# netbox_cli — Main Package

Core library: API client, CLI app, TUI app, config, schema, services, and shared utilities.

## Subpackages
- [`cli/`](cli/CLAUDE.md) — Typer CLI application split into focused modules
- [`ui/`](ui/CLAUDE.md) — Textual TUI application (app, panels, navigation, formatting, state)
- [`themes/`](themes/CLAUDE.md) — JSON theme files auto-discovered by `theme_registry.py`
- [`reference/openapi/`](reference/CLAUDE.md) — Bundled NetBox OpenAPI schema

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Package version (`0.1.0`) |
| `api.py` | Async `aiohttp` NetBox API client with caching and token fallback |
| `cli/` | Typer CLI subpackage — see `cli/CLAUDE.md` |
| `config.py` | Profile management (`~/.config/netbox-cli/config.json`) |
| `demo_auth.py` | Playwright-based demo.netbox.dev account/token provisioning |
| `docgen_capture.py` | Captures `nbx` CLI output and writes Markdown + JSON to `docs/generated/` |
| `docgen_specs.py` | `CaptureSpec` model and `all_specs()` — ordered list of commands to capture for docs |
| `http_cache.py` | Filesystem HTTP cache with TTL (fresh/stale-if-error) |
| `output_safety.py` | Strips ANSI escapes and control characters from terminal output |
| `schema.py` | Indexes the bundled OpenAPI JSON for groups, resources, paths, filters |
| `services.py` | Maps (group, resource, action, id) → (method, path, query, payload) |
| `theme_registry.py` | Loads, validates, and registers JSON themes with Textual |
| `trace_ascii.py` | Renders cable-trace JSON as Unicode box-drawing ASCII art |
| `tui.py` | Re-export shim: `NetBoxTuiApp`, `run_tui`, theme utilities from `ui/` |
| `dev_tui.py` | Re-export shim: `NetBoxDevTuiApp`, `run_dev_tui` from `ui/` |
| `logging_runtime.py` | Structured JSON logging setup; writes to `~/.config/netbox-cli/logs/netbox-cli.log` |
| `tui.tcss` | Main TUI Textual CSS — **all colors via semantic variables, never hardcoded hex** |
| `dev_tui.tcss` | Dev TUI Textual CSS — same semantic-variable contract |
| `logs_tui.tcss` | Logs viewer TUI Textual CSS — same semantic-variable contract |
| `ui_common.tcss` | Shared visual design layer imported by all three TUI stylesheets |

---

## api.py

Async HTTP client that wraps `aiohttp`. All NetBox calls go through here.

```python
client = NetBoxApiClient(config)
response = await client.request("GET", "/api/dcim/devices/", query={"limit": 50})
```

**Key behaviours:**
- `probe_connection()` — hits `/api/status/` to validate URL + token before any real call
- Token fallback — if v2 `Bearer nbt_<key>.<secret>` returns 403, retries with v1 `Token <secret>`
- Cache layer — delegates to `HttpCacheStore` before making network calls (60 s fresh, 300 s stale-if-error)
- `build_url(path)` — always builds from `config.base_url`, never allows relative escapes

**Error types:**
- `RequestError(RuntimeError)` — wraps non-2xx responses with status + body
- `ConnectionProbe.ok` — boolean probe result; `.error` carries human-readable message

---

## cli/ subpackage

Typer application (`app`) exposed as the `nbx` CLI entry point. Split into focused modules:

| Module | Purpose |
|---|---|
| `cli/__init__.py` | Root `app`, `main()`, static commands (`init`, `config`, `groups`, `resources`, `ops`, `call`, `tui`, `docs`), app wiring |
| `cli/runtime.py` | `_RUNTIME_CONFIGS`, `_SCHEMA_INDEX`, client/index factory functions |
| `cli/support.py` | `console`, `print_response`, `run_with_spinner`, Rich table rendering, theme resolution |
| `cli/demo.py` | `demo_app` — `nbx demo` command group (init, config, test, reset, tui) |
| `cli/dev.py` | `dev_app` — `nbx dev` command group + `nbx dev http` sub-app, Pydantic input models |
| `cli/dynamic.py` | `_handle_dynamic_invocation`, `_register_openapi_subcommands` |

**Structure standard:**
- Keep CLI modules inside `netbox_cli/cli/`.
- Treat the old flat layout (`cli.py`, `cli_runtime.py`, `cli_demo.py`, `cli_dynamic.py`, `cli_support.py`, `cli_dev.py`) as legacy only.
- Do not introduce new top-level `cli_*.py` modules under `netbox_cli/`.

**Import rules:**
- Root CLI app wiring belongs in `netbox_cli.cli` (`cli/__init__.py`).
- Import focused helpers from their package modules, for example:
  - `from netbox_cli.cli import app, main`
  - `from netbox_cli.cli.runtime import get_runtime_client`
  - `from netbox_cli.cli.support import print_response`
  - `from netbox_cli.cli.dynamic import _register_openapi_subcommands`
- Keep imports package-relative inside the `cli/` subpackage when modules depend on each other.

**Command groups:**

| Command | What it does |
|---|---|
| `nbx init` | Interactive first-time setup wizard |
| `nbx config` | Show active profile config |
| `nbx groups` | List all API groups from the OpenAPI schema |
| `nbx resources <group>` | List resources in a group |
| `nbx ops <group> <resource>` | Show available HTTP operations |
| `nbx <group> <resource> <action>` | **Dynamic command** — resolves to an API call |
| `nbx call <method> <path>` | Raw HTTP call (advanced) |
| `nbx tui` | Launch Textual TUI |
| `nbx logs` | View structured application logs in a TUI log viewer |
| `nbx demo init/config/test/reset` | Demo profile management via Playwright |
| `nbx dev tui` | Launch request-workbench dev TUI |
| `nbx docs generate-capture` | Run docgen capture pipeline |

**Dynamic command resolution:**
```
nbx dcim devices list --limit 10
  → GET /api/dcim/devices/?limit=10
```
Action → method mapping: `list`→GET, `get`→GET+id, `create`→POST, `update`→PUT, `patch`→PATCH, `delete`→DELETE.

**Pattern:** root `@app.callback()` loads config for every command except `init`, `tui`, `docs`, and `demo`.

---

## config.py

Manages named connection profiles persisted at `~/.config/netbox-cli/config.json`.

**Profile keys:** `base_url`, `token_version` (1 or 2), `token_key`, `token_secret`, `timeout`

**Environment variable overrides** (checked before disk):
- `NETBOX_URL` → `base_url`
- `NETBOX_TOKEN_KEY` → `token_key`
- `NETBOX_TOKEN_SECRET` → `token_secret`

**Security:** Config directory created with `0o700`, config file with `0o600`.

**Legacy migration:** Flat single-profile JSON is auto-migrated to multi-profile format on first load.

---

## http_cache.py

Filesystem cache at `~/.config/netbox-cli/http-cache/`. Keys are SHA-256 of `(base_url, method, path, query, auth_fingerprint)`.

| State | TTL |
|---|---|
| Fresh | 60 s (configurable via `CachePolicy`) |
| Stale-if-error | 300 s |

Supports conditional requests (ETag, Last-Modified) for bandwidth-efficient revalidation.

---

## schema.py

Loads the bundled `reference/openapi/netbox-openapi.json` once and provides query helpers.

```python
idx = SchemaIndex()
groups = idx.groups()             # ["circuits", "dcim", "ipam", ...]
resources = idx.resources("dcim") # ["cables", "devices", ...]
paths = idx.resource_paths("dcim", "devices")   # ResourcePaths(list="/api/dcim/devices/", detail="/api/dcim/devices/{id}/")
filters = idx.filter_params("dcim", "devices")  # [FilterParam(name="site", type="string"), ...]
```

Special helpers: `trace_path()` and `paths_path()` for cable-trace endpoints.

---

## services.py

Translates CLI invocations into `ResolvedRequest(method, path, query, payload)`:

```python
req = resolve_dynamic_request("dcim", "devices", "list", id=None, query={"limit": 10})
# → ResolvedRequest(method="GET", path="/api/dcim/devices/", query={"limit": 10}, payload=None)
```

Also provides `parse_key_value_pairs()` for `key=value` CLI argument lists and `load_json_payload()` for `--data` arguments.

---

## theme_registry.py

Discovers all `*.json` files under `netbox_cli/themes/`, validates structure, and registers with Textual's theme engine.

**Validation rules:**
- Required top-level keys: `name`, `label`, `dark`, `colors`
- `colors` must contain all 10 Textual semantic keys (`primary`, `secondary`, `warning`, `error`, `success`, `accent`, `background`, `surface`, `panel`, `boost`)
- `variables` must contain all 16 NetBox custom CSS variables (`nb-success-text`, `nb-info-text`, etc.)
- Color values must be `#RRGGBB` hex
- Name/alias collisions raise `ValueError`

**Catalog:**
```python
catalog = load_theme_catalog()
theme = catalog.resolve("netbox")   # resolves alias "netbox" → "netbox-dark"
names = catalog.names()             # ["default", "dracula", "netbox-dark", "netbox-light"]
```

**Theme enforcement contract:**
- Every Textual widget and subcomponent must render from the active theme tokens.
- Never ship fallback runtime palettes in Python or TCSS outside `themes/*.json`.
- Avoid built-in widget palettes when they bypass the app theme; prefer styling component classes in TCSS.

---

## trace_ascii.py

Converts NetBox cable-trace API response JSON into Unicode box-drawing art for terminal display.

```
┌────────────────┐
│  switch01      │
│  GigabitEth0/1 │ ───────── cable-01 ──────────
└────────────────┘
```

Functions:
- `render_cable_trace_ascii(trace_data)` — primary renderer
- `render_any_trace_ascii(trace_data)` — generic wrapper that calls `render_cable_trace_ascii`

---

## output_safety.py

Guards against terminal injection in any user-supplied or API-returned string displayed in the CLI.

```python
safe = sanitize_terminal_text(raw_string)   # ANSI stripped, control chars → U+FFFD
rt = safe_text(raw_string)                  # Rich Text object, safe to print
```

---

## docgen_capture.py

Generates `docs/generated/nbx-command-capture.md` and `docs/generated/raw/*.json` by running `nbx` commands through Typer's `CliRunner` in a headless subprocess-free way.

Key functions:
- `resolve_capture_paths(output, raw_dir)` — resolves output paths, defaults to `docs/generated/`
- `_inject_stub_config()` — populates the in-memory runtime config cache so commands don't prompt for setup
- `generate_command_capture_docs(output, raw_dir, max_lines, max_chars, use_demo)` — runs all `CaptureSpec` entries, writes Markdown

Invoked by:
- `nbx docs generate-capture` (CLI)
- `.github/workflows/docs.yml` (CI/CD)

---

## tui.tcss

Textual CSS stylesheet. **Never use hex colors here** — always semantic variables.

Key rules:
- `border: tall transparent` at rest so focus rings don't shift layout
- `.-loading` class drives spinner animation via CSS
- `.-active`, `.-error`, `.-expanded` modifier classes for state
- `layout: stream` + `align: left bottom` for log/feed views
- Block margin rhythm: `1 1 1 0`
