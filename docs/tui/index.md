# TUI Guide

The `nbx tui` command launches a full-screen interactive terminal application built with [Textual](https://textual.textualize.io/). It mirrors the NetBox web UI layout — navigation tree on the left, tabbed workspace in the center — and uses the same API client and schema index as the CLI.

---

## Launching the TUI

```bash
nbx tui                    # default profile
nbx tui --theme dracula    # specific theme
nbx tui --theme            # list available themes

nbx demo tui               # demo profile (demo.netbox.dev)
nbx demo tui --theme dracula
```

---

## Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Theme ▾   [search bar]                          NetBox CLI │
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

---

## Search

Press `/` to focus the top search bar. Typing filters the currently loaded results table in real time.

---

## State persistence

The TUI saves and restores:

- Last selected resource
- Applied filters
- Active theme

State is stored in `~/.config/netbox-cli/tui_state.json`.

---

## See also

- [Themes](themes.md) — built-in and custom themes
- [Keyboard Shortcuts](keybindings.md) — full key binding reference
