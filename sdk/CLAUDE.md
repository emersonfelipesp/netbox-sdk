# sdk — NetBox Python SDK

Standalone NetBox REST API client library. Zero dependency on `netbox_cli`, Typer, Textual, Rich, or Playwright. Can be used by any Python project that needs to talk to a NetBox instance over its REST API.

## Invariants

- **No `netbox_cli` imports.** Every module under `sdk/` must import only from `sdk.*`, stdlib, or third-party packages (`pydantic`, `aiohttp`, optional `pyyaml`). Any import of `netbox_cli` is a bug.
- **Typed.** `py.typed` marker is present (PEP 561). All public symbols are annotated.
- **Bundled schema.** `sdk/reference/openapi/netbox-openapi.json` ships with the package and is the default source for `build_schema_index()`.

---

## Package structure

```
sdk/
├── __init__.py           Public API — all exported symbols, __version__
├── config.py             Config model, profile persistence, auth headers, URL normalization
├── client.py             NetBoxApiClient, ApiResponse, RequestError, ConnectionProbe
├── http_cache.py         HttpCacheStore, CachePolicy, CacheEntry, build_cache_key
├── schema.py             SchemaIndex, Operation, ResourcePaths, FilterParam, OpenAPI loading
├── services.py           resolve_dynamic_request, run_dynamic_command, ResolvedRequest
├── plugin_discovery.py   discover_plugin_resource_paths
├── py.typed              PEP 561 marker
└── reference/
    └── openapi/
        └── netbox-openapi.json   Bundled NetBox OpenAPI schema (source of truth)
```

---

## Module map

| Module | Exports | Dependency |
|--------|---------|------------|
| `config.py` | `Config`, `load_profile_config`, `save_profile_config`, `authorization_header_value`, `resolved_token`, `config_path`, `cache_dir`, … | stdlib + pydantic |
| `http_cache.py` | `HttpCacheStore`, `CachePolicy`, `CacheEntry`, `build_cache_key` | stdlib + pydantic |
| `client.py` | `NetBoxApiClient`, `ApiResponse`, `RequestError`, `ConnectionProbe` | `sdk.config`, `sdk.http_cache`, aiohttp |
| `schema.py` | `SchemaIndex`, `Operation`, `ResourcePaths`, `FilterParam`, `build_schema_index`, `load_openapi_schema`, `parse_group_resource` | stdlib + pydantic, optional pyyaml |
| `services.py` | `resolve_dynamic_request`, `run_dynamic_command`, `ResolvedRequest`, `parse_key_value_pairs`, `load_json_payload`, `ACTION_METHOD_MAP` | `sdk.client`, `sdk.schema` |
| `plugin_discovery.py` | `discover_plugin_resource_paths` | `sdk.client` |

---

## Quick start

```python
import asyncio
from sdk import Config, NetBoxApiClient, build_schema_index

cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v2",
    token_key="your-key-id",
    token_secret="your-secret",
)

async def main():
    client = NetBoxApiClient(cfg)

    # Connection health check
    probe = await client.probe_connection()
    print(probe.version)   # "4.2"
    print(probe.ok)        # True

    # List resources
    response = await client.request("GET", "/api/dcim/devices/", query={"limit": 10})
    devices = response.json()["results"]

    # Create
    response = await client.request("POST", "/api/dcim/devices/", payload={"name": "sw01", ...})
    new_device = response.json()

    # GraphQL
    response = await client.graphql("{ device_list { id name } }")

asyncio.run(main())
```

---

## config.py

### Config model

```python
class Config(BaseModel):
    base_url: str | None       # "https://netbox.example.com"
    token_version: str         # "v1" or "v2" (default "v2")
    token_key: str | None      # v2 only: key prefix (without "nbt_")
    token_secret: str | None   # v2: secret suffix  |  v1: full token
    demo_username: str | None  # demo.netbox.dev credentials
    demo_password: str | None
    timeout: float             # HTTP timeout in seconds (default 30)
```

`base_url` is auto-normalized on assignment (strips trailing slashes, enforces https/http, rejects embedded credentials).

### Authentication

| Token version | Header format |
|---|---|
| v1 | `Token <secret>` |
| v2 | `Bearer nbt_<key>.<secret>` |

```python
from sdk.config import authorization_header_value, resolved_token

header = authorization_header_value(cfg)   # "Bearer nbt_mykey.mysecret"
token  = resolved_token(cfg)               # "nbt_mykey.mysecret"
```

### Profile storage

Profiles are stored at `~/.config/netbox-cli/config.json` (or `$XDG_CONFIG_HOME/netbox-cli/config.json`). Two built-in profiles: `"default"` and `"demo"`.

**Environment variable overrides** (applied for `DEFAULT_PROFILE` only):
- `NETBOX_URL` → `base_url`
- `NETBOX_TOKEN_KEY` → `token_key`
- `NETBOX_TOKEN_SECRET` → `token_secret`

```python
from sdk.config import load_profile_config, save_profile_config, DEFAULT_PROFILE

cfg = load_profile_config()         # loads "default" profile + env vars
save_profile_config("myprofile", cfg)
```

### Security

- Config directory created with `0o700`
- Config file written with `0o600` via `os.open` with atomic flags
- `base_url` validation rejects embedded credentials, FTP, non-HTTP schemes

---

## client.py

### NetBoxApiClient

```python
client = NetBoxApiClient(
    config,
    on_token_refresh=None,   # optional: callback for demo v1 token expiry
)
```

**`on_token_refresh`** — injectable callback invoked when a demo v1 token returns 401/403 with "Invalid v1 token". Signature:

```python
def my_refresh(config: Config) -> tuple[str | None, Config]:
    ...
    return new_auth_header, updated_config
```

The SDK has zero knowledge of `demo_auth.py`. The CLI layer injects this callback via `cli/runtime.py._demo_token_refresh_callback`.

### request()

```python
response = await client.request(
    method,          # "GET", "POST", "PUT", "PATCH", "DELETE"
    path,            # relative path, e.g. "/api/dcim/devices/"
    query=None,      # dict[str, str] — query params
    payload=None,    # dict | list — JSON body
    headers=None,    # extra headers
)
```

Returns `ApiResponse(status, text, headers)`. Call `response.json()` to parse JSON.

**Caching** — GET requests to `/api/...` paths are cached by `HttpCacheStore`:

| Endpoint type | Fresh TTL | Stale-if-error |
|---|---|---|
| List endpoints (`/api/group/resource/`) | 60 s | 300 s |
| Filtered GET (query params) | 30 s | 120 s |
| Detail endpoints | 15 s | 60 s |

Non-GET requests and `/api/status/` are never cached. Cache entries are keyed by `SHA-256(base_url + method + path + query + auth_fingerprint)`.

**Token fallback** — if v2 Bearer token returns 403 with "invalid v2 token", retries automatically with v1 `Token <secret>`.

**ETag/Last-Modified** — stale cache entries send `If-None-Match` / `If-Modified-Since`; 304 responses revalidate the entry.

### Other methods

```python
probe = await client.probe_connection()  # ConnectionProbe(ok, status, version, error)
version = await client.get_version()     # "4.2" or raises RequestError
response = await client.graphql("{ device_list { id name } }", variables={"id": 1})
url = client.build_url("/api/dcim/devices/")  # "https://netbox.example.com/api/dcim/devices/"
```

### Error types

```python
class RequestError(RuntimeError):
    response: ApiResponse   # .status, .text

class ConnectionProbe(BaseModel):
    ok: bool
    status: int
    version: str
    error: str | None
```

---

## http_cache.py

Filesystem cache at `~/.config/netbox-cli/http-cache/`. Files are private (`0o600`).

```python
store = HttpCacheStore(cache_dir())
key   = build_cache_key(base_url=..., method="GET", path=..., query=..., authorization=...)

entry = store.load(key)          # CacheEntry | None
entry = store.save(key, response, policy)
entry = store.refresh(key, entry, policy)
```

`CacheEntry` provides:
- `is_fresh(now)` — `now < fresh_until`
- `can_serve_stale(now)` — `now < stale_if_error_until`
- `response_parts(cache_status)` — `(status, text, headers)` with `X-NBX-Cache` injected

---

## schema.py

```python
idx = build_schema_index()         # loads sdk/reference/openapi/netbox-openapi.json
idx = build_schema_index(path)     # custom path (JSON or YAML)

idx.groups()                       # ["circuits", "dcim", "extras", "ipam", ...]
idx.resources("dcim")              # ["cables", "devices", "interfaces", ...]
idx.operations_for("dcim", "devices")  # [Operation(method="GET", path=...), ...]
idx.resource_paths("dcim", "devices")  # ResourcePaths(list_path=..., detail_path=...)
idx.filter_params("dcim", "devices")   # [FilterParam(name="q", type="string"), ...]
idx.trace_path("dcim", "interfaces")   # "/api/dcim/interfaces/{id}/trace/" | None
idx.paths_path("circuits", "circuit-terminations")  # "/api/.../paths/" | None
```

**Runtime plugin discovery** — augment the index from live `/api/plugins/` tree:

```python
idx.add_discovered_resource(
    group="plugins",
    resource="myplugin/widgets",
    list_path="/api/plugins/myplugin/widgets/",
    detail_path="/api/plugins/myplugin/widgets/{id}/",
)
idx.remove_group_resources("plugins")  # clean up all plugin entries
```

---

## services.py

Translates (group, resource, action, id) tuples into `ResolvedRequest(method, path, query, payload)`.

```python
req = resolve_dynamic_request(
    idx, "dcim", "devices", "list",
    object_id=None, query={"site": "lon"}, payload=None,
)
# ResolvedRequest(method="GET", path="/api/dcim/devices/", query={"site": "lon"})

response = await run_dynamic_command(
    client, idx, "dcim", "devices", "create",
    object_id=None,
    query_pairs=[],
    body_json='{"name": "sw01"}',
    body_file=None,
)
```

Action → HTTP method mapping:

| Action | Method | Requires `--id` |
|--------|--------|-----------------|
| `list` | GET | No |
| `get` | GET | Yes |
| `create` | POST | No |
| `update` | PUT | Yes |
| `patch` | PATCH | Yes |
| `delete` | DELETE | Yes |

---

## plugin_discovery.py

Walks the live `/api/plugins/` tree to find plugin collection/detail paths:

```python
paths = await discover_plugin_resource_paths(client)
# [("/api/plugins/gpon/olts/", "/api/plugins/gpon/olts/{id}/"), ...]
```

Returns `list[tuple[list_path, detail_path | None]]`. Each discovered path can be fed into `idx.add_discovered_resource()`.

---

## Relationship to netbox_cli

`netbox_cli/` re-exports all SDK symbols through thin shims for backward compatibility:

```
netbox_cli/api.py          → re-exports from sdk.client
netbox_cli/config.py       → re-exports from sdk.config
netbox_cli/http_cache.py   → re-exports from sdk.http_cache
netbox_cli/schema.py       → re-exports from sdk.schema
netbox_cli/services.py     → re-exports from sdk.services
netbox_cli/ui/plugin_discovery.py → re-exports from sdk.plugin_discovery
```

New code should import directly from `sdk.*`. The shims exist only for backward compatibility with existing `netbox_cli.*` imports.
