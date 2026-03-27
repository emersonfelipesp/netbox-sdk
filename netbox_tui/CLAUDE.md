# netbox_tui — TUI Package

`netbox_tui` is the Textual layer. It depends on `netbox_sdk` and `textual`.

## Package Contract

- `netbox_tui` owns all Textual apps, widgets, TCSS, themes, and the theme registry.
- `theme_registry.py` stays in `netbox_tui` because it depends on Textual theme types.
- Shared data formatting belongs in `netbox_sdk.formatting`, not here.

## Module Map

| File | Purpose |
|---|---|
| `app.py` | Main NetBox browser TUI |
| `cli_tui.py` | CLI-builder TUI |
| `dev_app.py` | Dev/workbench TUI |
| `logs_app.py` | Log viewer TUI |
| `django_model_app.py` | Django model inspector TUI |
| `chrome.py` | Shared theme/clock/logo/topbar helpers |
| `navigation.py`, `nav_blueprint.py` | Navigation model and blueprint |
| `widgets.py`, `panels.py` | Shared widgets and composed panels |
| `state.py`, `dev_state.py`, `django_model_state.py` | Persisted TUI state |
| `theme_registry.py` | Theme catalog loading/validation |
| `*.tcss` | Stylesheets packaged with the TUI |
| `themes/*.json` | Built-in theme definitions |

## Import Rules

- Import API/config/schema/formatting helpers from `netbox_sdk.*`.
- Do not import from removed `netbox_cli.ui.*` paths.
- If the TUI needs CLI runtime helpers, import from `netbox_cli` or `netbox_cli.runtime`, not old `netbox_cli.cli.*` paths.

## Packaging

- Extra required for this package: `.[tui]`
- Package data includes `*.tcss` and `themes/*.json`
