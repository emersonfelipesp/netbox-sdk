# TUI Guide

NetBox SDK ships multiple Textual applications. The main entry point is
`nbx tui`, a full-screen browser for NetBox resources that shares the same
config, API client, and schema index as the CLI and Python SDK.

Other TUI entry points specialize in development, logs, guided command
composition, GraphQL exploration, and Django model inspection:

- `nbx tui` for the main browser
- `nbx dev tui` for the developer workbench
- `nbx graphql tui` for interactive GraphQL schema browsing and query execution
- `nbx cli tui` for guided command assembly
- `nbx tui logs` for the full-screen logs viewer
- `nbx logs` for the plain CLI log tail
- `nbx dev django-model tui` for contributor-facing model inspection

The main TUI also discovers plugin resources dynamically. If a NetBox plugin
exposes a REST API under `/api/plugins/`, `nbx tui` and `nbx dev tui` can add
those resources to the sidebar automatically and load their data like any
built-in NetBox resource.

---

## Launching the TUI

```bash
nbx tui                    # default profile
nbx tui --theme dracula    # specific theme
nbx tui --theme            # list available themes

nbx demo tui               # demo profile (demo.netbox.dev)
nbx demo tui --theme dracula

nbx dev tui                # developer request workbench
nbx demo dev tui           # developer request workbench on demo.netbox.dev
nbx graphql tui            # GraphQL explorer and query runner
nbx demo graphql tui       # GraphQL explorer against demo.netbox.dev
nbx cli tui                # guided command builder
nbx tui logs               # full-screen logs viewer
nbx logs                   # plain CLI log tail
```

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Theme ▾   [search bar]                          NetBox SDK │
├────────────────┬────────────────────────────────────────────┤
│  Navigation    │  Results  │ Details │ Filters              │
│                │                                            │
│  ▼ circuits    │  [Results table]                           │
│  ▼ core        │                                            │
│  ▼ dcim        │                                            │
│    ▸ devices   │  [Detail panel when row selected]          │
│    ▸ sites     │                                            │
│    ▸ …         │                                            │
│  ▼ ipam        │                                            │
│    ▸ prefixes  │                                            │
│    ▸ …         │                                            │
│                │                                            │
├────────────────┴────────────────────────────────────────────┤
│  Status bar / help hints                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Tabs

### Results

The main data view. Selecting a resource in the navigation tree loads its objects into the results table. Rows are rendered with prioritized columns (`id`, `name`, `status`, `site`, `role`, …).

- Press `Space` to toggle selection on a row.
- Press `A` to toggle all visible rows.
- Press `D` or click a row to open its detail view.

### Details

Shows the full object attributes as a key-value panel. For `dcim/interfaces` with a connected cable, an ASCII cable trace diagram is rendered below the attributes.

### Filters

A form for applying API query filters to the current resource. Press `F` to open the filter modal.

---

## Navigation tree

The left panel shows all NetBox app groups as expandable sections. Click a resource to load its list, or use keyboard navigation:

- `G` — focus the navigation tree
- Arrow keys — move through nodes
- `Enter` — select / expand a node

### Plugin resources

Plugin REST resources are appended under a `Plugins` menu automatically when the connected NetBox instance exposes them under `/api/plugins/`.

- no hardcoded plugin list is required
- plugin resources appear in both `nbx tui` and `nbx dev tui`
- if the plugin exposes list/detail REST endpoints, the TUI can browse and render the returned data just like built-in resources

---

## Search

Press `/` to focus the top search bar. Typing filters the currently loaded results table in real time.

---

## State persistence

The TUI saves and restores:

- Last selected resource
- Applied filters
- Active theme

State is stored under the NetBox SDK config root, typically
`~/.config/netbox-sdk/tui_state.json`. Older `netbox-cli` state files are still
read automatically when present.

---

## See also

- [Developer Workbench](dev-workbench.md)
- [GraphQL TUI](graphql.md)
- [CLI Builder](cli-builder.md)
- [Logs Viewer](logs.md)
- [Django Models Browser](django-models.md)
- [Launch Command Output](../reference/tui/launch-examples/index.md)
- [Themes](themes.md)
- [Keyboard Shortcuts](keybindings.md)
