# netbox_cli/ui — Textual TUI Application

This subpackage contains the full Textual TUI. Every module here is UI-layer oriented: no direct HTTP calls, and only lightweight local UI-state persistence. All runtime data comes through `NetBoxApiClient` and `SchemaIndex` from the parent package.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Public re-exports: `NetBoxTuiApp`, `NetBoxDevTuiApp`, `NbxCliTuiApp`, `DjangoModelTuiApp`, `NetBoxLogsTuiApp`, theme helpers, `run_tui`, `run_dev_tui`, `run_cli_tui`, `run_django_model_tui`, `run_logs_tui` |
| `app.py` | `NetBoxTuiApp` — root Textual `App[None]` with layout, data loading, and event handling |
| `cli_tui.py` | `NbxCliTuiApp` — interactive CLI command builder TUI (`nbx cli tui`); navigable group→resource→action tree that constructs and runs `nbx` commands |
| `cli_completions.py` | `CliCommandNode` and `nbx_root_command_nodes()` — builds the full navigation tree from `SchemaIndex` for the CLI builder TUI |
| `dev_app.py` | `NetBoxDevTuiApp` — request workbench / API dev shell |
| `django_model_app.py` | `DjangoModelTuiApp` — Django model inspector TUI (`nbx dev django-model tui`); browse models, relationships, ASCII diagrams, and source code |
| `django_model_state.py` | Persistent state models and JSON storage helpers for the Django Model Inspector TUI |
| `chrome.py` | Shared theme, logo, clock, and connection-badge behavior |
| `filter_overlay.py` | `FilterOverlayMixin` — filter picker dialog, overlay, and active-filter display logic |
| `formatting.py` | Field/value humanization and Rich `Text` semantic styling |
| `nav_blueprint.py` | `NAV_BLUEPRINT` — static menu data mirroring NetBox sidebar ordering |
| `navigation.py` | `NavMenu`/`NavGroup`/`NavItem` models and `build_navigation_menus()` |
| `dev_rendering.py` | Stateless Rich `Text` rendering helpers for the dev TUI (method/status styles, request lines) |
| `logo_render.py` | `build_netbox_logo()` — renders the themed NetBox wordmark as a Rich `Text` object |
| `logs_app.py` | `NetBoxLogsTuiApp` — structured JSON log viewer TUI (`nbx logs`) |
| `panels.py` | `ObjectAttributesPanel` — detail view with key/value table + cable trace |
| `plugin_discovery.py` | `discover_plugin_resource_paths()` — runtime walk of `/api/plugins/` to find collection endpoints |
| `widgets.py` | Shared composition primitives: `NbxButton`, `NbxPanelHeader`, `NbxPanelBody`, `ContextBreadcrumb`, `SupportModal` |
| `state.py` | `TuiState` persistence to `~/.config/netbox-cli/tui_state.json` |
| `dev_state.py` | `DevTuiState`, `DevViewState`, `RequestExecution` — dev TUI state and request data |

---

## app.py — NetBoxTuiApp

The main `App[None]` subclass. Manages layout, reactive bindings, and async workers.

### Composition Rule

Build UI the way React builds components:

- small reusable widgets
- explicit constructor props
- nested `compose()` trees
- composition preferred over inheritance for layout reuse

Example:

- `NbxButton("Send", tone="primary", size="medium")`
- `ObjectAttributesPanel` composed from `NbxPanelHeader` + `NbxPanelBody`

### Layout Structure
```
#topbar         ← theme selector | app title | connection state | ContextBreadcrumb | support btn | close btn
#query_bar      ← search input | filter action
#sidebar        ← navigation tree (groups → resources)
#results_tab    ← DataTable of list results
#detail_panel   ← ObjectAttributesPanel (attributes + cable trace)
```

### Key Bindings

| Key | Action |
|---|---|
| `q` | Quit |
| `/` | Focus search input |
| `g` | Focus navigation tree |
| `s` | Focus results table |
| `r` | Refresh current view |
| `f` | Open filter modal |
| `space` | Toggle row selection |
| `a` | Select all rows |
| `d` | Show detail panel |
| `escape` | Cancel / close modal (also closes open breadcrumb menu) |
| `Ctrl+G` | Clear log viewer |

### Async Data Loading
Uses Textual's `@work` decorator for background async tasks. Workers call `NetBoxApiClient.request()` and post `Message` objects back to the main thread to update widgets. Never `await` directly in `on_*` handlers.

### State Persistence
On mount: `load_tui_state()` restores last view (group, resource) and theme.
On quit/navigation change: `save_tui_state()` persists current state.

### Demo Mode
When launched with `--demo` flag (or via `nbx demo init`), the app operates in **read-only** mode: create/update/delete actions are disabled.

### Theme Switching
Theme switching goes through shared helpers in `chrome.py`: the selector resolves the name, `apply_theme()` updates the active theme and shared semantic styles, and the new theme name is persisted via `save_tui_state()`. `_sync_screen_theme_classes()` ensures the new theme CSS class is applied to every screen in the stack (including open modals), not just the topmost screen.

### ContextBreadcrumb
The topbar context widget is `ContextBreadcrumb` (from `widgets.py`), not a plain `Static`. It renders the current navigation path as clickable segments. Clicking a group segment opens a scoped `OptionList` dropdown of sibling resources; selecting an option navigates directly. Plugin resources get a three-level crumb: `Plugins › <plugin> › <resource>`. Messages: `CrumbSelected`, `MenuOptionSelected`.

### SupportModal
Both main and dev TUIs have a "Liked it? Support me!" button in the topbar. Pressing it pushes a shared `SupportModal` (`ModalScreen`) that displays the GitHub Sponsors URL. The modal inherits the active theme class on mount so it renders correctly after a runtime theme switch.

---

## formatting.py

Pure functions for converting raw API field names and values into human-readable form for the TUI.

### Key Functions

```python
humanize_identifier("ip_address")   # → "IP Address"
humanize_field("last_updated")      # → "Last Updated"
humanize_value({"id": 1, "name": "nyc01"})  # → "nyc01 (#1)"
key_value_rows(obj)                 # → [(field_label, rendered_value), ...]
order_field_names(fields)           # → sorted with priority fields first
semantic_cell(value, field)         # → Rich Text with semantic color
```

### Field Priority Order
`id → name → display → label → status → type → role → site → location → device → interface → ip → address → prefix → vlan → tenant → description → created → last_updated → url`

### Semantic Colors (from theme variables)
| Color | Used for |
|---|---|
| `nb-id-text` | ID values |
| `nb-key-text` | Key/slug values |
| `nb-muted-text` | Null / empty values |
| `nb-link-text` | URL values |
| `nb-success-text` | Active/operational status |
| `nb-danger-text` | Failed/inactive status |
| `nb-warning-text` | Warning status |

---

## navigation.py

Defines the static navigation menu that mirrors the NetBox sidebar. No dynamic content — all items are hardcoded from the NetBox information architecture.

### Structure
```
NavMenu(label)
  └── NavGroup(label)
        └── NavItem(label, group, resource)
```

### Top-Level Menus
- **Organization** → Regions, Site Groups, Sites, Locations, Contact Groups, Contacts, Tenants
- **Racks** → Rack Roles, Rack Types, Racks, Reservations
- **Devices** → Platforms, Device Types, Manufacturers, Devices, Modules, Inventory Items
- **Cabling** → Cables, Interfaces, Front/Rear Ports, Console Ports, Power Ports
- **Power** → Power Panels, Power Feeds
- **Inventory** → Inventory Item Roles, Inventory Items
- **IPAM** → Prefixes, IP Ranges, IP Addresses, VLANs, VRFs, Route Targets, ASNs
- **VPN** → Tunnels, Tunnel Groups, L2VPN, VXLAN
- **Circuits** → Providers, Provider Accounts, Circuit Types, Circuits, Circuit Terminations
- **Tenancy** → Tenant Groups, Tenants, Contact Groups, Contacts, Contact Roles
- **Wireless** → Wireless LANs, Wireless Links
- **Custom** → Custom Fields, Custom Field Choices, Config Contexts, Tags
- **Admin** → Users, Tokens, Webhooks, Journals

When adding new NetBox resources: add a `NavItem` in the correct menu/group here. The `group` and `resource` must match what `SchemaIndex.resources()` returns.

---

## panels.py

UI components for the detail view on the right side of the TUI.

### ObjectAttributesPanel
Renders a selected object as a two-column `DataTable` (Field | Value) plus an optional cable trace section.

**Loading state machine:**
```
mount             → adds .-loading class → spinner visible
data arrives      → removes .-loading  → spinner hidden, attributes shown
cable trace found → trace section title unhidden, ASCII art rendered
```

**Spinner frames:** `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` (cycles via `set_interval`)

**Cable trace integration:**
- Checks if selected object has a `/trace/` endpoint via `SchemaIndex.trace_path()`
- If yes, fires async worker to call `GET /api/<resource>/{id}/trace/`
- Passes result to `render_any_trace_ascii()` and displays in a `Static` widget

---

## state.py

Lightweight JSON persistence for TUI session state.

**File:** `~/.config/netbox-cli/tui_state.json`

`state.py` uses Pydantic models, not dataclasses:

```python
class ViewState(BaseModel):
    group: str | None = None
    resource: str | None = None
    query_text: str = ""
    details_expanded: bool = False

class TuiState(BaseModel):
    last_view: ViewState = Field(default_factory=ViewState)
    theme_name: str | None = None
```

```python
state = load_tui_state()   # returns defaults if file missing/corrupt
save_tui_state(state)      # atomic write
```

**Defaults if file missing:**
- `theme_name = None` and the runtime theme catalog resolves to `netbox-dark` when available
- `last_view = ViewState()` with empty group/resource/query values

---

## chrome.py

Shared helpers used by both the main TUI and the dev TUI.

| Function | Purpose |
|---|---|
| `get_theme_catalog()` | Returns the singleton `ThemeCatalog` |
| `initialize_theme_state()` | Registers the active theme with Textual on app mount |
| `apply_theme(app, name)` | Switches to a new theme; calls `_sync_screen_theme_classes()` to update every screen in the stack |
| `_sync_screen_theme_classes(app, ...)` | Adds/removes `theme-<name>` CSS classes on all screens in `app.screen_stack` (deduped by `id()`) |
| `logo_renderable()` | Returns a themed Rich `Text` NetBox logo |
| `refresh_logo_widget()` | Rerenders the logo widget after a theme switch |
| `strip_theme_select_prefix()` | Removes the theme prefix from `Select` option labels |
| `update_clock_widget()` | Updates the HH:MM clock `Static` |
| `set_connection_badge_state()` | Sets `-checking`, `-ok`, or `-error` CSS class on the connection badge |
| `badge_state_for_probe()` | Maps a `ConnectionProbe` result to a badge state string |

---

## plugin_discovery.py

Async runtime discovery of NetBox plugin REST endpoints.

```python
paths = await discover_plugin_resource_paths(client)
# → [("plugins", "/api/plugins/gpon/ont-profiles/"), ...]
```

Walks `/api/plugins/` response recursively, identifies collection endpoints (returns `{"count": …, "results": […]}`), and returns `(group, list_path)` pairs. These are used by `navigation.py` to append plugin resources to the nav tree without hardcoding them.

---

## logs_app.py

`NetBoxLogsTuiApp` — a read-only TUI log viewer launched by `nbx logs`.

- Reads structured JSON log entries from `~/.config/netbox-cli/logs/netbox-cli.log`
- Displays entries in a `DataTable`; selecting a row shows the full JSON detail
- `Ctrl+G` clears the log file (after confirmation) and refreshes the view
- Theming follows the same contract as the main TUI: all colors from semantic variables

---

## logo_render.py

Single function: `build_netbox_logo(theme: ThemeDefinition) -> Text`

Constructs the `"NetBox"` wordmark as a Rich `Text` object with theme-driven colors (`nb-logo-wordmark`, `nb-logo-accent`). Called by `chrome.logo_renderable()`.

---

## widgets.py — Full Primitive Reference

| Class / Constant | Purpose |
|---|---|
| `SPONSOR_URL` | `"https://github.com/sponsors/emersonfelipesp"` — single source of truth |
| `NbxButton` | Themed Textual `Button` with `tone`, `size`, `chrome` semantic props |
| `NbxPanelHeader` | Panel header bar composed from a `Static` title |
| `NbxPanelBody` | Panel body container with optional `tone` and `surface` |
| `_CrumbButton` | Internal breadcrumb nav button — do not instantiate outside `ContextBreadcrumb` |
| `ContextBreadcrumb` | Clickable breadcrumb bar; emits `CrumbSelected` and `MenuOptionSelected` |
| `SupportModal` | Shared GitHub Sponsors modal — themed, used in main and dev TUIs |
