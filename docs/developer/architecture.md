# Architecture

`netbox-cli` is organized around a shared API client and OpenAPI schema index that power both the CLI (Typer) and the TUI (Textual) from the same data layer.

---

## Module map

```
netbox_cli/
├── cli.py              Typer app — all commands, dynamic registration, profile dispatch
├── api.py              Async aiohttp HTTP client (ApiResponse, NetBoxApiClient)
├── config.py           Profile storage, env overrides, token normalization
├── schema.py           OpenAPI schema loading and indexing (SchemaIndex)
├── services.py         Request resolution and action mapping (run_dynamic_command)
├── demo_auth.py        Playwright automation for demo.netbox.dev token retrieval
├── docgen_capture.py   CLI output capture and Markdown generation
├── theme_registry.py   Theme discovery, validation, and catalog management
├── trace_ascii.py      ASCII cable trace renderer
├── tui.py              Thin wrapper — re-exports run_tui from ui.app
└── ui/
    ├── app.py          NetBoxTuiApp — main Textual application
    ├── formatting.py   Response parsing, humanization, semantic cell rendering
    ├── navigation.py   Navigation tree building from SchemaIndex
    ├── panels.py       ObjectAttributesPanel — detail view with cable trace
    └── state.py        TUI state persistence (last resource, filters, theme)
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
_print_response()          Rich table or raw JSON/YAML
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
_load_resource_list()     @work(thread=True)
    │
    ▼
client.request("GET", list_path)
    │
    ▼
parse_response_rows()     formatting.py
    │
    ▼
DataTable (Results tab)
    │
    ▼ (row selected)
_load_object_details()    @work(thread=False)
    │
    ├── client.request("GET", detail_path)
    └── _load_trace_for_object()   (dcim/interfaces only)
            │
            ▼
        render_cable_trace_ascii()   trace_ascii.py
            │
            ▼
        panel.set_trace()   ObjectAttributesPanel
```

---

## Profile system

Profiles are named configs stored in a single JSON file. Two profiles are currently defined: `default` and `demo`.

```python
# config.py
DEFAULT_PROFILE = "default"
DEMO_PROFILE    = "demo"
DEMO_BASE_URL   = "https://demo.netbox.dev"
```

In `cli.py`, the in-process cache is a dict:

```python
_RUNTIME_CONFIGS: dict[str, Config] = {}
```

Profile loading sequence (for `_ensure_profile_config(profile)`):

1. Check `_RUNTIME_CONFIGS[profile]` — return immediately if complete.
2. Call `load_profile_config(profile)` — reads from disk + env vars.
3. If still incomplete and `profile == DEMO_PROFILE` → call `_initialize_demo_profile()`.
4. If still incomplete for default profile → interactive prompt.
5. Save result to `_RUNTIME_CONFIGS[profile]`.

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

---

## API client

`api.py` wraps `aiohttp` with:

- `ApiResponse` dataclass: `status: int`, `text: str`, `headers: dict`
- `NetBoxApiClient.request()`: builds URL, attaches `Authorization` header, handles v2→v1 token retry on 401/403
- `NetBoxApiClient.probe_connection()`: `GET /api/` for health checks

---

## Dynamic command registration

`_register_openapi_subcommands(target_app, *, client_factory, index_factory)` runs at module import time (twice — once for root `app`, once for `demo_app`):

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

The `client_factory` parameter is what separates the default and demo command trees: `_get_client` for `app`, `_get_demo_client` for `demo_app`.
