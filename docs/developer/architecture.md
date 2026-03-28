# Architecture

The repository is organized as three sibling Python packages:

- `netbox_sdk` — standalone API/SDK layer
- `netbox_cli` — Typer CLI layer
- `netbox_tui` — Textual TUI layer

## Dependency Direction

```text
netbox_cli  -> netbox_sdk
netbox_tui  -> netbox_sdk
netbox_cli  -> netbox_tui   only via lazy imports for TUI-launching commands
netbox_sdk  -/-> netbox_cli, netbox_tui
```

`netbox_sdk` is the stable core. It must remain importable without Typer or Textual installed.

## Package Layout

```text
netbox_sdk/
  __init__.py
  client.py
  config.py
  http_cache.py
  schema.py
  services.py
  plugin_discovery.py
  formatting.py
  logging_runtime.py
  output_safety.py
  trace_ascii.py
  demo_auth.py
  django_models/
  reference/openapi/netbox-openapi.json

netbox_cli/
  __init__.py
  runtime.py
  dynamic.py
  support.py
  demo.py
  dev.py
  django_model.py
  markdown_output.py
  docgen_capture.py
  docgen_specs.py
  docgen/

netbox_tui/
  __init__.py
  app.py
  cli_tui.py
  dev_app.py
  logs_app.py
  django_model_app.py
  chrome.py
  navigation.py
  nav_blueprint.py
  panels.py
  widgets.py
  state.py
  dev_state.py
  django_model_state.py
  filter_overlay.py
  theme_registry.py
  *.tcss
  themes/*.json
```

## Responsibilities

### `netbox_sdk`

Owns:
- API client behavior
- profile/config loading
- HTTP caching
- OpenAPI schema indexing
- request resolution
- plugin discovery helpers
- shared formatting and output safety
- demo auth helpers
- Django model parsing/cache helpers

### `netbox_cli`

Owns:
- `nbx` entrypoint
- top-level command registration
- runtime config/index/client factories
- dynamic command wiring from OpenAPI
- CLI output rendering and markdown output
- demo/dev/doc generation command trees

CLI commands that launch a TUI must lazy-import `netbox_tui` and surface an install hint for `pip install 'netbox-sdk[tui]'` when needed.

### `netbox_tui`

Owns:
- all Textual applications
- shared Textual widgets/chrome/panels/state
- TCSS assets
- theme registry and theme JSON catalog

Shared data transformation such as `semantic_cell`, `humanize_value`, and row parsing lives in `netbox_sdk.formatting`, not in the TUI package.

## Data Flow

### CLI

```text
nbx dcim devices list
  -> netbox_cli.__init__.py root app
  -> netbox_cli.dynamic
  -> netbox_sdk.services.resolve_dynamic_request
  -> netbox_sdk.client.NetBoxApiClient.request
  -> netbox_cli.support / markdown_output
```

### TUI

```text
nbx tui
  -> netbox_cli lazy-imports netbox_tui
  -> netbox_tui.app.NetBoxTuiApp
  -> netbox_sdk.client / schema / formatting
  -> Textual widgets + TCSS + theme registry
```

## Packaging

- Core install: `pip install netbox-sdk`
- CLI install: `pip install 'netbox-sdk[cli]'`
- TUI install: `pip install 'netbox-sdk[tui]'`
- Full install: `pip install 'netbox-sdk[all]'`

## Verification

For architecture-affecting changes, run:

```bash
uv sync --dev --extra cli --extra tui --extra demo
uv run pre-commit run --all-files
uv run pytest
```
