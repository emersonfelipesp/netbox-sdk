# netbox_cli/ui — Textual TUI Application

This subpackage contains the full Textual TUI. Every module here is UI-layer only — no direct HTTP calls, no config I/O. All data comes through `NetBoxApiClient` and `SchemaIndex` from the parent package.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Public re-exports: `NetBoxTuiApp`, `run_tui`, `available_theme_names`, `resolve_theme_name` |
| `app.py` | `NetBoxTuiApp` — root Textual `App[None]` with all widgets and event handling |
| `formatting.py` | Field/value humanization and Rich `Text` semantic styling |
| `navigation.py` | Static nav menu structure (mirrors NetBox UI sidebar) |
| `panels.py` | `ObjectAttributesPanel` — detail view with key/value table + cable trace |
| `widgets.py` | Shared composition primitives like `NbxButton`, `NbxPanelHeader`, `NbxPanelBody` |
| `state.py` | `TuiState` persistence to `~/.config/netbox-cli/tui_state.json` |

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

- `NbxButton("Send", variant="primary", size="medium")`
- `ObjectAttributesPanel` composed from `NbxPanelHeader` + `NbxPanelBody`

### Layout Structure
```
#topbar         ← search input | theme selector | app title
#nav            ← navigation tree (groups → resources)
#results        ← DataTable of list results
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
| `escape` | Cancel / close modal |

### Async Data Loading
Uses Textual's `@work` decorator for background async tasks. Workers call `NetBoxApiClient.request()` and post `Message` objects back to the main thread to update widgets. Never `await` directly in `on_*` handlers.

### State Persistence
On mount: `load_tui_state()` restores last view (group, resource) and theme.
On quit/navigation change: `save_tui_state()` persists current state.

### Demo Mode
When launched with `--demo` flag (or via `nbx demo init`), the app operates in **read-only** mode: create/update/delete actions are disabled.

### Theme Switching
Theme selector widget at `#topbar` calls `resolve_theme_name()` then `self.app.register_theme()` + `self.app.theme = name`. The new theme name is persisted via `save_tui_state()`.

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

```python
@dataclass
class ViewState:
    group: str
    resource: str
    query_text: str
    details_expanded: bool

@dataclass
class TuiState:
    last_view: ViewState | None
    theme_name: str
```

```python
state = load_tui_state()   # returns defaults if file missing/corrupt
save_tui_state(state)      # atomic write
```

**Defaults if file missing:**
- `theme_name = "default"`
- `last_view = None`
