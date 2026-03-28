# Architecture

`netbox-cli` is organized around a shared API client and OpenAPI schema index that power both the CLI (Typer) and the TUI (Textual) from the same data layer.

For distribution names (`netbox-console` / `netbox-sdk`), import boundaries, and `app_runtime`, see [Package integration](package-integration.md). For SOLID-style conventions, see [Design principles](design-principles.md).

In addition to the bundled OpenAPI schema, the TUI runtime can augment the schema index by discovering live plugin REST resources exposed under `/api/plugins/`. This lets plugin-backed resources appear in the TUI automatically when a plugin implements a full REST API.

The TUI theme system is part of the architecture, not decoration: every Textual widget and subcomponent must derive its runtime styling from the active theme catalog, with no hardcoded colors or stray Textual defaults outside `netbox_cli/themes/*.json`.

---

## Module map

```
netbox_cli/
├── cli/                Typer CLI subpackage
│   ├── __init__.py     Root app, main(), re-exports for tests/embedders
│   ├── commands/       Static command registration (profile, http_api, tui, subapps, …)
│   ├── runtime.py      Profile prompts, demo repair, Typer verification helpers
│   ├── support.py      Console output, Rich table rendering, theme resolution
│   ├── demo.py         nbx demo command group (init, config, test, reset, tui)
│   ├── dev.py          nbx dev command group + nbx dev http sub-app
│   └── dynamic.py      _register_openapi_subcommands, _handle_dynamic_invocation
├── app_runtime.py      Typer-free get_schema_index / client_for_config / get_default_client
├── api.py              Async aiohttp HTTP client (ApiResponse, NetBoxApiClient)
├── config.py           Profile storage, env overrides, token normalization
├── profile_cache.py    In-process _RUNTIME_CONFIGS shared by api, CLI, docgen
├── schema.py           OpenAPI schema loading and indexing (SchemaIndex)
├── services.py         Request resolution and action mapping (run_dynamic_command)
├── http_cache.py       Filesystem HTTP cache with TTL (60 s fresh, 300 s stale-if-error)
├── demo_auth.py        Playwright automation for demo.netbox.dev token retrieval
├── docgen_capture.py   CLI output capture and Markdown generation
├── docgen_specs.py     CaptureSpec model + all_specs() ordered command list
├── logging_runtime.py  Structured JSON logging setup (→ logs/netbox-cli.log)
├── output_safety.py    ANSI escape and control-char sanitization
├── theme_registry.py   Theme discovery, validation, and catalog management
├── trace_ascii.py      ASCII cable trace renderer
├── tui.py              Thin wrapper — re-exports run_tui from ui.app
├── dev_tui.py          Thin wrapper — re-exports run_dev_tui from ui.dev_app
├── tui.tcss            Main TUI stylesheet (semantic variables only)
├── dev_tui.tcss        Dev TUI stylesheet (semantic variables only)
├── logs_tui.tcss       Log viewer TUI stylesheet (semantic variables only)
├── ui_common.tcss      Shared visual design layer imported by all three TUI stylesheets
└── ui/
    ├── app.py              NetBoxTuiApp — main Textual application
    ├── dev_app.py          NetBoxDevTuiApp — request workbench application
    ├── chrome.py           Shared theme / clock / logo / connection chrome helpers
    ├── filter_overlay.py   FilterOverlayMixin — filter picker dialog and overlay logic
    ├── formatting.py       Response parsing, humanization, semantic cell rendering
    ├── logo_render.py      build_netbox_logo() — themed NetBox wordmark (Rich Text)
    ├── logs_app.py         NetBoxLogsTuiApp — structured log viewer (nbx logs)
    ├── nav_blueprint.py    NAV_BLUEPRINT — static menu data mirroring NetBox sidebar
    ├── navigation.py       NavMenu/NavGroup/NavItem models, build_navigation_menus()
    ├── plugin_discovery.py Runtime /api/plugins/ discovery for plugin REST resources
    ├── panels.py           ObjectAttributesPanel — detail view with cable trace
    ├── widgets.py          Shared composition primitives: NbxButton, NbxPanelHeader,
    │                       NbxPanelBody, ContextBreadcrumb, SupportModal
    ├── state.py            Main TUI state persistence (tui_state.json)
    ├── dev_state.py        Dev TUI state persistence
    └── dev_rendering.py    Stateless Rich Text rendering helpers for the dev TUI
```

---

## Data flow: CLI

```
nbx dcim devices list
        │
        ▼
root_callback()            ensure default profile config is loaded
        │
        ▼
_register_openapi_subcommands()   (runs at import time)
    reads SchemaIndex → builds Typer sub-apps for every group/resource/action
        │
        ▼
_command() [generated]     Typer command for "list" on dcim/devices
        │
        ▼
_execute_dynamic_action()
        │
        ▼
run_dynamic_command()      services.py — resolves path, calls client.request()
        │
        ▼
NetBoxApiClient.request()  api.py — async aiohttp GET with Bearer token
        │
        ▼
_print_response()          Rich table or raw JSON/YAML/Markdown
```

---

## Data flow: TUI

```
nbx tui
        │
        ▼
tui_command()
        │
        ▼
run_tui(client, index, theme)
        │
        ▼
NetBoxTuiApp.run()        Textual event loop
        │
    ┌───┴────────────────────────────────┐
    │                                    │
    ▼                                    ▼
on_tree_node_selected()          on_key() / bindings
    │
    ▼
_load_rows()              @work — list: services.resolve_dynamic_request(..., "list") + GET
    │
    ▼
parse_response_rows()     formatting.py
    │
    ▼
DataTable (Results tab)
    │
    ▼ (row selected)
_load_object_details()    @work — get: resolve_dynamic_request(..., "get", id) + GET
    │
    ├── _show_detail_for_path() (linked objects may pass explicit paths)
    └── _load_trace_for_object()   trace/paths templates + GET
            │
            ▼
        render_cable_trace_ascii()   trace_ascii.py
            │
            ▼
        panel.set_trace()   ObjectAttributesPanel
```

---

## UI Composition Pattern

The TUI follows a React-style composition model for Textual widgets:

- small reusable widgets act like component primitives
- constructor arguments act like props
- larger views assemble those primitives in `compose()`
- composition is preferred over inheritance for layout reuse

Examples in the current codebase:

- `NbxButton` standardizes size and theme props such as `tone`
- `NbxPanelHeader` and `NbxPanelBody` define reusable panel structure with prop-like theme inputs
- `ObjectAttributesPanel` composes those primitives instead of inheriting layout from a base panel class
- `ContextBreadcrumb` renders the topbar navigation context as clickable segments with dropdown menus, emitting typed `CrumbSelected`/`MenuOptionSelected` messages — no static parent references
- `SupportModal` is a self-contained `ModalScreen` shared by both TUIs, themed from the active app theme via a CSS class synced on mount

Contributor guideline: when adding new UI, first ask "can this be expressed as nested reusable widgets?" before introducing a new base class.

---

## Profile system

Profiles are named configs stored in a single JSON file. Two profiles are currently defined: `default` and `demo`.

```python
# config.py
DEFAULT_PROFILE = "default"
DEMO_PROFILE    = "demo"
DEMO_BASE_URL   = "https://demo.netbox.dev"
```

The in-process profile dict lives in `profile_cache.py` (re-exported from `cli.runtime` for compatibility):

```python
# profile_cache.py
_RUNTIME_CONFIGS: dict[str, Config] = {}
```

Profile loading sequence (for `_ensure_profile_config(profile)` in `cli/runtime.py`):

1. Check `_RUNTIME_CONFIGS[profile]` — return immediately if complete.
2. Call `load_profile_config(profile)` — reads from disk + env vars.
3. If still incomplete and `profile == DEMO_PROFILE` → call `_initialize_demo_profile()`.
4. If still incomplete for default profile → interactive prompt.
5. Save result via `_cache_profile(profile, cfg)` (updates `_RUNTIME_CONFIGS`).

---

## OpenAPI schema indexing

`schema.py` loads `reference/openapi/netbox-openapi.json` at startup and builds a `SchemaIndex`:

```python
@dataclass
class SchemaIndex:
    def groups() -> list[str]                    # all app groups
    def resources(group) -> list[str]            # resources for a group
    def operations_for(group, resource)          # list of Operation objects
    def resource_paths(group, resource)          # ResourcePaths (list + detail)
    def trace_path(group, resource) -> str|None  # /api/.../trace/ if available
```

`Operation` holds: `group`, `resource`, `method`, `path`, `operation_id`, `summary`.

`ResourcePaths` holds: `list_path` (`/api/group/resources/`) and `detail_path` (`/api/group/resources/{id}/`).

For plugin resources, `SchemaIndex` also supports runtime augmentation. The TUI can discover plugin list/detail endpoints from the live `/api/plugins/` tree and add them into the shared index so they behave like normal resources in navigation, request resolution, and rendering.

---

## API client

`api.py` wraps `aiohttp` with:

- `ApiResponse` dataclass: `status: int`, `text: str`, `headers: dict`
- `NetBoxApiClient.request()`: builds URL, attaches `Authorization` header, handles v2→v1 token retry on 401/403
- `NetBoxApiClient.probe_connection()`: `GET /` with `API-Version` header for health checks

---

## Dynamic command registration

`_register_openapi_subcommands(target_app, *, client_factory, index_factory)` in `cli/dynamic.py` runs at module import time (twice — once for root `app`, once for `demo_app`):

```python
for group in index.groups():
    group_typer = Typer(...)
    target_app.add_typer(group_typer, name=group)

    for resource in index.resources(group):
        resource_typer = Typer(...)
        group_typer.add_typer(resource_typer, name=resource)

        for action in _supported_actions(group, resource):
            cmd = _build_action_command(group, resource, action, client_factory, index_factory)
            resource_typer.command(name=action)(cmd)
```

The `client_factory` parameter is what separates the default and demo command trees: default profile uses `_runtime_get_client` (resolves via `netbox_cli.cli`), while `demo_app` uses factories defined in `cli/commands/__init__.py` that call `_ensure_demo_runtime_config` and `_get_client_for_config` at invocation time (so tests can patch `cli` / `runtime` predictably).
