# netbox_cli — CLI Package

`netbox_cli` is the Typer-based command layer. It depends on `netbox_sdk` and optionally on `netbox_tui` for commands that launch Textual applications.

## Package Contract

- `import netbox_cli` must work with only the `cli` extra installed.
- Any command path that launches a TUI must lazy-import `netbox_tui` and raise a clear install hint if `textual` is unavailable.
- No old `netbox_cli/cli/` or `netbox_cli/ui/` paths remain in active code.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Root Typer app, `main()`, top-level command registration, script entrypoint target |
| `runtime.py` | Runtime config cache, schema loading, client factories, demo refresh wiring |
| `dynamic.py` | OpenAPI-driven dynamic command registration and execution |
| `support.py` | Shared CLI rendering, output selection, TUI lazy-import helpers |
| `demo.py` | `nbx demo ...` command tree |
| `dev.py` | `nbx dev ...` command tree |
| `django_model.py` | Django model CLI commands |
| `markdown_output.py` | Markdown rendering helpers |
| `docgen_capture.py` / `docgen_specs.py` / `docgen/` | Documentation capture pipeline |

## Import Rules

- Import SDK types/functions from `netbox_sdk.*`.
- Import TUI entrypoints only inside function bodies unless the module is explicitly TUI-only.
- Keep root app references on `netbox_cli`, for example:
  - `from netbox_cli import app, main`
  - `from netbox_cli.runtime import _get_client, _get_index`
  - `from netbox_cli.dynamic import _register_openapi_subcommands`

## Packaging

- Console entrypoint: `nbx = netbox_cli:main`
- Extra required for this package: `.[cli]`
- TUI-launching commands additionally require `.[tui]`
