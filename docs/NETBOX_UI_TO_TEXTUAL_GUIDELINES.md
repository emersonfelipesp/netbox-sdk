# NetBox UI to Textual TUI Design Guidelines

This document summarizes how NetBox's frontend is built and defines a practical porting strategy to a Textual-based TUI in `netbox-cli`.

## 1. NetBox Frontend Architecture (What Exists Today)

## 1.1 Stack and Build

NetBox's web UI is built from:

- Django templates (server-rendered HTML)
- SCSS -> bundled CSS
- TypeScript -> bundled JavaScript
- HTMX for partial page updates
- Bootstrap/Tabler/TomSelect UI primitives

Primary references:

- `netbox/docs/development/web-ui.md`
- `netbox/netbox/project-static/src/*.ts`
- `netbox/netbox/project-static/styles/*.scss`
- `netbox/netbox/templates/**/*.html`

## 1.2 Runtime Page Skeleton

Core page composition comes from:

- `templates/base/base.html`: global assets, theme bootstrap, JS boot, message container
- `templates/base/layout.html`: sidebar, top search bar, content area, footer, modals

NetBox UI consistently uses these zones:

- Left navigation sidebar (grouped menus)
- Top search/input zone
- Main content area (tabs + cards + tables/forms)
- Footer/status line
- Modal overlay container

## 1.3 UI as Declarative Components (Python-side)

A key NetBox design choice is that page content is not only raw templates; it is composed from Python UI classes:

- `netbox/ui/layout.py`: `Layout -> Row -> Column`
- `netbox/ui/panels.py`: reusable `Panel` abstractions
- `netbox/ui/attrs.py`: typed object attributes (text, choice, bool, nested object, image, etc.)
- app-level panel declarations, e.g. `dcim/ui/panels.py`

This declarative composition is important for TUI parity because it naturally maps to Textual widget composition.

## 1.4 List/Detail Interaction Model

Common pages:

- List view: `templates/generic/object_list.html`
- Detail view: `templates/generic/object.html`

List pages include:

- quick search
- filters tab
- sortable/paged table
- bulk selection/actions
- table configuration

Detail pages include:

- breadcrumbs + object identity
- action buttons (edit/delete/bookmark/etc.)
- tabbed sections
- panel grid (rows/columns/cards)

## 1.5 Dynamic/Partial Updates

NetBox uses HTMX heavily for table refreshes and modal content:

- `templates/htmx/table.html`
- `templates/inc/table_htmx.html`
- `templates/inc/table_controls_htmx.html`
- `templates/inc/htmx_modal.html`
- `project-static/src/htmx.ts`

Pattern: user interaction updates just the needed fragment; client-side listeners are re-initialized after swap.

## 1.6 Frontend State and Behavior

Notable behavior modules:

- `src/netbox.ts`: central initialization pipeline
- `src/sidenav.ts`: sidebar state + pin/unpin + responsive behavior
- `src/hotkeys.ts`: global hotkeys (e.g. `/` focuses search)
- `src/search.ts`: quicksearch UX
- `src/tableConfig.ts`: table preference persistence via API
- `src/colorMode.ts` + `js/setmode.js`: light/dark mode persistence
- `src/state/index.ts`: localStorage-backed state manager

## 1.7 Visual System

SCSS structure:

- `styles/_variables.scss`: fonts, spacing, colors, sidebar width
- `styles/netbox.scss`: imports (base + overrides + transitional + custom)
- `styles/transitional/*`: compatibility layer for common UI primitives

Visual semantics are token-based (variables first), not ad-hoc inline styling.

## 2. Porting Principles for Textual

## 2.1 Preserve Information Architecture First

Do not start from widgets. Start from NetBox page semantics:

- Navigation hierarchy (menu/group/item)
- List workflows (search/filter/sort/paginate/bulk)
- Detail workflows (panels + tabs + actions)
- Feedback patterns (alerts/toasts/status)

In Textual, this becomes:

- App shell with persistent left nav + top command/search + content body + footer
- Screen modes for list/detail/edit/actions
- Shared panel widgets for consistent object rendering

## 2.2 Map NetBox Primitives to Textual Primitives

Suggested mapping:

- Sidebar menu -> `Tree` or `ListView` with grouped sections
- Tabs -> `TabbedContent` + `TabPane`
- Cards/Panels -> custom `Widget` containers with title/action row
- Attribute tables -> two-column `DataTable` or key/value list widget
- Object list tables -> `DataTable` with sort/filter state
- Modal dialogs -> `ModalScreen`
- Toast/messages -> notification widget + footer status channel
- HTMX partial swap -> targeted widget refresh/update methods

## 2.3 Recreate Incremental Refresh Behavior

HTMX's partial updates should become widget-level async refresh:

- Never reload full screen for small table/filter changes
- Keep separate workers for:
  - table data
  - filter metadata
  - side nav counts (optional)
- Re-render only changed regions (`DataTable` rows/cells set-diff)

## 2.4 Keep CLI/TUI Backend Shared

NetBox web and API separate presentation from data. Do the same:

- one API service layer (already in `netbox_cli/api.py` + `services.py`)
- CLI and TUI call same service methods
- no TUI-specific business logic for CRUD semantics

## 2.5 Treat Theme as Tokens

Mirror NetBox token strategy in Textual CSS variables:

- define base color tokens (surface, panel, accent, danger, muted)
- define layout tokens (sidebar width, panel spacing)
- support light/dark switch persisted in local config (similar to NetBox color mode persistence)

## 3. Concrete Porting Blueprint for netbox-cli

## 3.1 Shell Layout

Create a root app shell that mirrors `base/layout.html`:

- left nav pane: app/resource hierarchy
- top bar: global quick search + active context
- main pane: dynamic content (list/detail/edit)
- footer: status, connection, server time, active profile

## 3.2 Navigation Model

NetBox menu backend is permission-filtered and grouped (`navigation/menu.py`, `templatetags/navigation.py`).

TUI equivalent:

- build menu tree from OpenAPI groups/resources now
- later enrich with API-driven permissions and user profile
- per-item quick actions equivalent to menu buttons (add/import)

## 3.3 List Screen Contract

For every resource list screen:

- Quick search input (key `/` to focus, matching web UX)
- Filter panel (toggleable side panel or tab)
- Sortable/paged `DataTable`
- Bulk selection model (select visible/select all matching)
- Action bar (add/export/bulk edit/delete)

Keep list state in an explicit local store object analogous to NetBox's frontend state:

- query
- applied filters
- ordering
- page/per_page
- selected IDs
- visible columns

## 3.4 Detail Screen Contract

For each object detail:

- breadcrumb/context line
- title + object identifier
- primary action buttons
- tab strip for auxiliary views
- panel grid from declarative panel specs

Implement panel classes in TUI analogous to NetBox `Panel` classes:

- `ObjectAttributesPanelWidget`
- `RelatedObjectsPanelWidget`
- `JsonPanelWidget`
- `ObjectsTablePanelWidget`

## 3.5 Attribute Rendering Layer

NetBox has typed attributes in `ui/attrs.py`. Recreate this idea:

- a small TUI attribute renderer registry:
  - text
  - numeric + unit
  - choice/status badge
  - boolean
  - nested object path
  - JSON
- central placeholder behavior for null values

This avoids per-screen formatting drift.

## 3.6 Modal and Quick-Add Patterns

NetBox uses `htmx_modal` + quick-add flows. Textual equivalent:

- use `ModalScreen` for create/edit dialogs
- on save success:
  - update source widget (e.g., select options, table rows)
  - close modal
  - show notification

## 3.7 Message and Error Semantics

NetBox toasts and server messages should map to:

- non-blocking notifications for success/info
- sticky error panel for failures
- footer transient status for background operations

For API errors, display:

- HTTP status
- parsed `detail`/validation payload
- retry hint/action

## 3.8 Hotkeys and Accessibility

Port critical keyboard behavior first:

- `/` focus search
- `g` focus groups/nav
- `s` focus resource table
- `r` refresh current view
- `q` quit/back depending context
- modal escape handling

Avoid keybindings that conflict with text input focus.

## 4. What Not to Port 1:1

Do not clone web-specific details that have no TUI value:

- Bootstrap class semantics
- pixel-based responsive breakpoints
- browser-specific popovers/tooltips behavior
- DOM swap events

Port the *workflow intent*, not HTML mechanics.

## 5. Minimum Viable Parity Milestones

1. Navigation parity
- OpenAPI group/resource tree + command palette/search jump

2. List parity
- query/filter/sort/page/bulk selection for top resources (`dcim.devices`, `ipam.prefixes`, `ipam.ip-addresses`)

3. Detail parity
- object header + panelized attributes + related objects table

4. Action parity
- create/edit/delete and common bulk actions

5. UX parity
- theme tokens, notifications, hotkeys, persistent preferences

## 6. Implementation Notes for netbox-cli

Immediate recommendations:

- Introduce `netbox_cli/ui/` package with panel and screen abstractions (mirroring NetBox's `ui/` layering)
- Add a local state module for list/detail view state persistence
- Standardize response -> table/attr transformation utilities to keep CLI/TUI formatting consistent
- Keep one API contract path and avoid branching logic between CLI and TUI

This approach preserves NetBox's proven UX structure while adopting Textual-native interaction patterns.
