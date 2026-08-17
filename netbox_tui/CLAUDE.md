# netbox_tui — TUI Package

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-sdk/netbox_tui/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/netbox-sdk.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

`netbox_tui` is the Textual layer. It depends on `netbox_sdk` and `textual`.

## Release-line pin

`NetBoxTuiApp` and `run_tui()` take a `pinned_line` argument, passed down by
`netbox_cli` from `--netbox-version` / `NETBOX_SDK_NETBOX_VERSION`. The TUI does
not resolve release lines itself; it receives a `SchemaIndex` the CLI already
resolved.

The pin exists because of the **post-login reload**:
`_reload_schema_for_authenticated_client()` rebuilds the schema after an
interactive login, and must rebuild it against the line the TUI was launched
with. Resolving unpinned there would silently swap contracts — a 4.5-pinned TUI
connected to a 4.6 instance would come back describing 4.6 while the CLI and MCP
surfaces stayed on 4.5. Use `netbox_sdk.schema_resolution.resolve_index(client,
line=self._pinned_line)`, never a bare `fetch_schema_for_client()`.


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
| `dev_app.py` | Dev/workbench TUI; every POST/PUT/PATCH/DELETE send requires an explicit per-request confirmation modal showing the method, path, and payload before dispatch |
| `filter_overlay.py` | Shared filter modal/overlay behavior |
| `graphql_app.py` | GraphQL explorer TUI |
| `login_modal.py` | Login/profile prompt modal |
| `logs_app.py` | Log viewer TUI |
| `django_model_app.py` | Django model inspector TUI |
| `proxbox_app.py` | Proxbox-only request workbench entrypoint backed by the stable Proxbox catalog and the shared per-write confirmation modal |
| `chrome.py` | Shared theme/clock/logo/topbar helpers |
| `navigation.py`, `nav_blueprint.py` | Navigation model and blueprint |
| `cli_completions.py` | `CliCommandNode` model and `nbx_root_command_nodes()` — builds the full command-tree for the CLI-builder TUI, including generated Proxbox command branches |
| `dev_rendering.py` | Stateless Rich `Text` rendering helpers for the dev workbench TUI (HTTP method styles, status codes, operation lines) |
| `lifecycle.py` | Shared async `close_client_for_tui()` helper used by all Textual app `on_unmount` handlers |
| `logo_render.py` | Theme-aware Rich renderable for the NetBox wordmark (`build_netbox_logo()`) used in the top bar |
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
