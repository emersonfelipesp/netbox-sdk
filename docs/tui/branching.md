# Branching

When the [`netbox-branching`](https://github.com/netboxlabs/netbox-branching)
plugin is installed on the target NetBox, the main TUI grows two extra
touchpoints:

## Ctrl+B — Branch switcher

A global keybinding opens a modal listing all branches. Use the arrow keys
and **Enter** to activate one; **Escape** dismisses without changes. The
first entry, **"main (no active branch)"**, clears the active branch.

```
┌── Switch Branch ─────────────────────────────────────────┐
│ Enter to activate · Escape to cancel                     │
│                                                          │
│   main (no active branch)                                │
│ ● td5smq0f · feature-x   [ready]                         │
│   ab12cd34 · hotfix      [merged]                        │
└──────────────────────────────────────────────────────────┘
```

## Topbar pill

When a branch is active, a coloured **`● <schema_id> · <name>`** pill is
mounted in the topbar (left of the breadcrumb). On `main` (no active branch)
no pill is shown — the topbar stays unchanged. The pill is removed entirely
when the plugin is not installed.

## Persistence

The active branch is persisted to the per-base-URL `tui_state.*.json` file
under your config directory. The next time the TUI starts against the same
NetBox host, the branch is re-applied automatically.

If feature detection later reports the plugin has been removed, the
persisted state is cleared on startup.

## How the header propagates

Activating a branch writes the `X-NetBox-Branch` header onto the SDK
client's `persistent_headers` dict. Every request — including those spawned
by background Textual `@work` tasks — picks up the header, so list reloads,
detail panels, and dynamic resource browsers all stay consistent with the
active branch.
