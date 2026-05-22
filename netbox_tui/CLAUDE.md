# netbox_tui — TUI Package

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_tui/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

`netbox_tui` is the Textual layer. It depends on `netbox_sdk` and `textual`.

## Package Contract

- `netbox_tui` owns all Textual apps, widgets, TCSS, themes, and the theme registry.
- `theme_registry.py` stays in `netbox_tui` because it depends on Textual theme types.
- Shared data formatting belongs in `netbox_sdk.formatting`, not here.

## Module Map

| File | Purpose |
|---|---|
| `app.py` | Main NetBox browser TUI |
| `branch_screen.py` | Branch switcher overlay and branch selection workflow |
| `cli_tui.py` | CLI-builder TUI |
| `dev_app.py` | Dev/workbench TUI |
| `filter_overlay.py` | Shared filter modal/overlay behavior |
| `graphql_app.py` | GraphQL explorer TUI |
| `login_modal.py` | Login/profile prompt modal |
| `logs_app.py` | Log viewer TUI |
| `django_model_app.py` | Django model inspector TUI |
| `chrome.py` | Shared theme/clock/logo/topbar helpers |
| `navigation.py`, `nav_blueprint.py` | Navigation model and blueprint |
| `plugin_discovery.py` | TUI-facing plugin discovery helpers |
| `ssl_verify_support.py` | TLS verification prompt/support helpers |
| `widgets.py`, `panels.py` | Shared widgets and composed panels |
| `state.py`, `dev_state.py`, `django_model_state.py`, `graphql_state.py` | Persisted TUI state |
| `theme_registry.py` | Theme catalog loading/validation |
| `*.tcss` | Stylesheets packaged with the TUI |
| `themes/*.json` | Built-in theme definitions |

## Import Rules

- Import API/config/schema/formatting helpers from `netbox_sdk.*`.
- Do not import from removed `netbox_cli.ui.*` paths.
- If the TUI needs CLI runtime helpers, import from `netbox_cli` or `netbox_cli.runtime`, not old `netbox_cli.cli.*` paths.
- Keep the TUI decoupled from the generated typed SDK unless a screen explicitly needs versioned typed models; the default TUI data path remains `netbox_sdk` client/facade utilities.
- Keep branch-aware UI state at the TUI boundary and pass branch scope to SDK/CLI helpers rather than duplicating HTTP behavior.

## Packaging

- Extra required for this package: `.[tui]`
- Package data includes `*.tcss` and `themes/*.json`

## Logging

- Use `netbox_sdk.logging_runtime.get_logger(__name__)` so file logging is configured consistently with the CLI.
- Long-running `@work` tasks and optional network paths should log **DEBUG** on recoverable failures (with `exc_info=True` when useful) instead of swallowing exceptions silently.
- Never log secrets (tokens, passwords); user-facing `notify()` strings should avoid echoing raw credentials.
