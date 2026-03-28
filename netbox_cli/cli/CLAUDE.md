# netbox_cli/cli — CLI Subpackage

Typer-based CLI application for `nbx`. Split into focused modules to keep each file under ~300 lines.

## Module Map

| File | Purpose |
|---|---|
| `__init__.py` | Root `app`, `main()`, re-exports (`run_dynamic_command`, config helpers) for tests; calls `commands.register_static_commands` |
| `commands/` | Static Typer command registration: `profile`, `schema_discovery`, `http_api`, `tui_launch`, `subapps`, `_wiring` (lazy `cli` resolution) |
| `runtime.py` | Profile prompts, demo repair, `_ensure_*_runtime_config`; schema index via `app_runtime.get_schema_index`; re-exports `profile_cache` symbols |
| `support.py` | CLI output helpers: `console`, `print_response`, `run_with_spinner`, Rich table rendering, theme resolution, cable-trace printing |
| `demo.py` | `demo_app` Typer sub-app — `nbx demo` commands: `init`, `config`, `test`, `reset`, `tui` |
| `dev.py` | `dev_app` Typer sub-app — `nbx dev` commands including `nbx dev http` sub-app and Pydantic input models |
| `dynamic.py` | `_handle_dynamic_invocation`, `_register_openapi_subcommands` — free-form `nbx <group> <resource> <action>` routing |
| `django_model.py` | `django_model_app` Typer sub-app — `nbx dev django-model` commands: `build`, `tui`, `fetch` |

## Dependency Direction

```
__init__.py
  ├── runtime.py     ←── support.py
  │     └── (lazy) demo.py
  ├── demo.py        ←── runtime.py, support.py
  │     └── (lazy) dynamic.py
  ├── dev.py         ←── runtime.py, support.py
  │     └── django_model.py
  ├── django_model.py ←── netbox_cli.django_models.*
  └── dynamic.py     ←── runtime.py, support.py
```

Circular import between `runtime.py` and `demo.py` is broken with a lazy import inside `_ensure_profile_config()`.
Circular import between `demo.py` and `dynamic.py` is broken with a lazy import inside `demo_callback()`.

## External entry points

- `netbox_cli.cli.app` — the root Typer app (used by tests and `pyproject.toml` `[project.scripts]`)
- `netbox_cli.cli.main` — the programmatic entry point
- `netbox_cli.cli._RUNTIME_CONFIGS` — re-export of `netbox_cli.profile_cache._RUNTIME_CONFIGS` (docgen workers inject config here)
