# SDK Internals

This page explains how `netbox_sdk` works under the hood — the HTTP client lifecycle, config and profile system, OpenAPI schema indexing, the facade object hierarchy, versioned typed clients, filesystem HTTP cache, and the services layer.

---

## NetBoxApiClient Request Lifecycle

`NetBoxApiClient` in `netbox_sdk/client.py` is the central async HTTP client. Every request passes through the same pipeline regardless of which API layer (raw, facade, or typed) initiated it.

```mermaid
sequenceDiagram
    participant Caller as Caller code
    participant Client as NetBoxApiClient
    participant Cache as HttpCacheStore
    participant Session as aiohttp.ClientSession
    participant NB as NetBox API

    Caller->>Client: request("GET", "/api/dcim/devices/", query={...})
    Client->>Client: _normalize_request_path() — SSRF guard
    Client->>Client: authorization_header_value() — build auth header
    Client->>Client: _cache_policy() — determine TTL policy
    Client->>Cache: load(cache_key)
    alt Cache FRESH (within TTL)
        Cache-->>Client: CacheEntry
        Client-->>Caller: ApiResponse (X-NBX-Cache: HIT)
    else Cache STALE or MISS
        alt Stale entry exists
            Client->>Client: add If-None-Match / If-Modified-Since headers
        end
        Client->>Client: _get_session() — lazy aiohttp session
        Client->>Session: session.request(GET, url, ...)
        Session->>NB: HTTPS GET
        NB-->>Session: 200 {...} or 304 Not Modified
        Session-->>Client: raw response
        alt 401/403 with v2 token
            Client->>Session: retry with Token fallback header
        end
        Client->>Cache: save(key, entry, policy)
        Client-->>Caller: ApiResponse
    end
```

### Lazy Session Creation

The `aiohttp.ClientSession` is created on the first request and reused for all subsequent calls. A double-check lock pattern handles event-loop affinity:

```python title="netbox_sdk/client.py"
async def _get_session(self) -> aiohttp.ClientSession:
    current_loop_id = id(asyncio.get_running_loop())

    # Fast path: session already valid for this loop — no lock needed
    if (
        self._session is not None
        and not self._session_closed()
        and self._session_loop_id == current_loop_id
    ):
        return self._session

    async with self._get_lock():
        # Re-check under lock in case another coroutine just created the session
        if self._session is None or session_closed or self._session_loop_id != current_loop_id:
            ...
            self._session = aiohttp.ClientSession(timeout=..., connector=...)
            self._session_loop_id = current_loop_id
        return self._session
```

### SSRF Protection

All request paths pass through `_normalize_request_path()`, which rejects absolute URLs, query strings, and fragments embedded in the path argument:

```python title="netbox_sdk/client.py"
def _normalize_request_path(self, path: str) -> str:
    parsed = urlsplit(path.strip())
    if parsed.scheme or parsed.netloc:
        raise ValueError("Request path must be relative to the configured NetBox base URL")
    if parsed.query or parsed.fragment:
        raise ValueError("Request path must not include query parameters or fragments")
    return parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
```

### v2-to-v1 Token Fallback

When a v2 `nbt_` token receives a 401/403 with "invalid v2 token" in the body, the client retries transparently with a `Token <secret>` v1 header:

```python title="netbox_sdk/client.py"
def _should_retry_with_v1(self, response: ApiResponse) -> bool:
    if self.config.token_version != "v2" or not self.config.token_secret:
        return False
    if response.status not in {401, 403}:
        return False
    return "invalid v2 token" in response.text.lower()
```

---

## Config and Profile System

`Config` in `netbox_sdk/config.py` is a Pydantic model that normalizes and validates connection parameters before passing them to `NetBoxApiClient`.

### Fields and Validators

| Field | Type | Description |
|---|---|---|
| `base_url` | `str \| None` | NetBox base URL — normalized to `http://` or `https://` only |
| `token_version` | `str` | `"v1"` (legacy `Token`) or `"v2"` (`nbt_` bearer) |
| `token_key` | `str \| None` | v2 token key prefix (before `.`) |
| `token_secret` | `str \| None` | Token value — CR/LF/null stripped to prevent header injection |
| `timeout` | `float` | HTTP timeout in seconds (default: 30.0) |
| `ssl_verify` | `bool` | TLS certificate verification (default: `True`) |
| `demo_username` | `str \| None` | Username for demo profile auto-login |
| `demo_password` | `str \| None` | Password for demo profile auto-login |

Validators strip control characters from token values and reject URLs with embedded credentials.

### Multi-Profile Persistence

Profiles are stored as `{"profiles": {"default": {...}, "demo": {...}}}` in `~/.config/netbox-sdk/config.json` with `0o600` permissions (owner read/write only):

```python title="netbox_sdk/config.py (pattern)"
# Load the active profile
config = load_profile_config(profile="default")

# Save updated credentials
save_config(config, profile="default")
```

### Environment Variable Override

| Variable | Config field |
|---|---|
| `NETBOX_URL` | `base_url` |
| `NETBOX_TOKEN_KEY` | `token_key` |
| `NETBOX_TOKEN_SECRET` | `token_secret` |
| `NETBOX_SSL_VERIFY` | `ssl_verify` |
| `DEMO_USERNAME` | `demo_username` |
| `DEMO_PASSWORD` | `demo_password` |

Environment variables take precedence over the profile config file.

---

## SchemaIndex (OpenAPI Parsing)

`SchemaIndex` in `netbox_sdk/schema.py` parses the bundled OpenAPI JSON into an in-memory index optimized for fast group/resource/operation lookups.

```mermaid
flowchart LR
    JSON["netbox-openapi-4.5.json\n(bundled)"]
    BUILD["SchemaIndex._build()\nparse all paths"]
    OPS["_operations\nlist[Operation]"]
    RPATHS["_resource_paths\ndict[group+resource → ResourcePaths]"]
    GROUPS["groups() → list[str]"]
    RES["resources(group) → list[str]"]
    OPFOR["operations_for(group, resource) → list[Operation]"]
    FILTER["filter_params(group, resource) → list[FilterParam]"]

    JSON --> BUILD
    BUILD --> OPS
    BUILD --> RPATHS
    OPS --> GROUPS
    OPS --> RES
    OPS --> OPFOR
    RPATHS --> FILTER
```

### Path Parsing

`parse_group_resource()` splits any NetBox API path into a `(group, resource)` tuple:

- `/api/dcim/devices/` → `("dcim", "devices")`
- `/api/plugins/my-plugin/widgets/` → `("plugins", "my-plugin/widgets")`
- `/api/ipam/ip-addresses/{id}/` → `("ipam", "ip-addresses")`

### Plugin Discovery

`enrich_schema_index_with_runtime_resources()` is the preferred high-level call: it walks the live `/api/plugins/` endpoint, parses each discovered path, and calls `add_discovered_resource()` on the supplied index. It returns `True` if the index changed.

```python
from netbox_sdk.plugin_discovery import enrich_schema_index_with_runtime_resources

changed = await enrich_schema_index_with_runtime_resources(schema_index, client)
# True when at least one new resource was registered
```

For lower-level control, `discover_plugin_resource_paths()` returns a list of `(list_path, detail_path)` tuples:

```python
from netbox_sdk.plugin_discovery import discover_plugin_resource_paths

paths = await discover_plugin_resource_paths(client)
# [("/api/plugins/gpon/olts/", "/api/plugins/gpon/olts/{id}/"), ...]

for list_path, detail_path in paths:
    # parse group/resource from list_path and call add_discovered_resource manually
    ...
```

### Versioned Bundled Schemas

Versioned OpenAPI schemas ship with the package under `netbox_sdk/reference/openapi/`. `load_openapi_schema()` defaults to the NetBox 4.6 schema unless a supported release line is supplied explicitly.

| File | NetBox Version |
|---|---|
| `netbox-openapi.json` | Legacy compatibility alias |
| `netbox-openapi-4.6.json` | NetBox 4.6 |
| `netbox-openapi-4.5.json` | NetBox 4.5 |
| `netbox-openapi-4.4.json` | NetBox 4.4 |
| `netbox-openapi-4.3.json` | NetBox 4.3 |

---

## Facade Object Hierarchy

`netbox_sdk/facade.py` provides a PyNetBox-compatible async API. The `api()` factory builds the root `Api` object; subsequent attribute accesses create `App` → `Endpoint` → `Record` / `RecordSet` objects.

```mermaid
flowchart TB
    APIFN["api(url, token)\nfactory function"]
    API["Api\n.client · .schema · .dcim · .ipam · …"]
    APP["App('dcim')\n__getattr__ → Endpoint"]
    ENDPOINT["Endpoint('devices')\n.all() · .filter() · .get() · .create()"]
    RECORDSET["RecordSet\nasync iterator · auto-pagination"]
    RECORD["Record\nattribute access · dirty tracking\n.save() · .delete()"]

    APIFN --> API
    API -->|".dcim"| APP
    APP -->|".devices"| ENDPOINT
    ENDPOINT -->|".all()"| RECORDSET
    RECORDSET -->|"async for item in …"| RECORD
    ENDPOINT -->|".get(id)"| RECORD
    ENDPOINT -->|".create(payload)"| RECORD
```

### CRUD Operations

```python title="netbox_sdk/facade.py (usage)"
nb = api("https://netbox.example.com", token="...")

# List all — async iteration with auto-pagination
async for device in nb.dcim.devices.all():
    print(device.name, device.status)

# Filter with query params
records = nb.dcim.devices.filter(site="nyc-dc1", status="active")
async for device in records:
    print(device)

# Get single by ID
device = await nb.dcim.devices.get(42)

# Create
tag = await nb.extras.tags.create({
    "name": "proxmox",
    "slug": "proxmox",
    "color": "ff5722",
})

# Get or create via facade (using lookup keywords)
result = await nb.extras.tags.get(slug="proxmox")
```

### Record Dirty Tracking

`Record` captures a snapshot of field values at creation time. Mutating a field adds it to a `_updates` dict; calling `.save()` sends only the changed fields as a PATCH:

```python title="netbox_sdk/facade.py (usage)"
device = await nb.dcim.devices.get(42)
device.status = "offline"          # marks "status" dirty
device.comments = "decommissioned" # marks "comments" dirty
await device.save()                 # PATCH {status, comments} only
```

### Specialized Record Types

| Type | Resource | Extras |
|---|---|---|
| `TraceableRecord` | DCIM interfaces, power ports, etc. | `.trace()` → cable trace result |
| `PathableRecord` | Circuit terminations | `.paths()` → path list |
| `DeviceRecord` | `dcim.devices` | `.render_config()`, `.napalm()` |

---

## Typed API (Versioned Clients)

`typed_api()` in `netbox_sdk/typed_api.py` returns a version-specific typed client backed by generated Pydantic models for full IDE completion and runtime validation.

```python title="Usage"
from netbox_sdk import typed_api

nb = typed_api("https://netbox.example.com", token="...", netbox_version="4.5")

# Full Pydantic validation on request and response
device = await nb.dcim.devices.retrieve(42)
device.name    # str — IDE knows the type
device.status  # DeviceStatus enum
```

### Version Selection

The `netbox_version` argument maps to a dynamically imported module:

```python title="netbox_sdk/typed_api.py (simplified)"
def typed_api(url, token, *, netbox_version):
    normalized = normalize_netbox_version(netbox_version)  # "4.6" / "4.5" / "4.4" / "4.3"
    suffix = version_module_suffix(normalized)             # "v4_6" / "v4_5" / "v4_4" / "v4_3"
    module = import_module(f"netbox_sdk.typed_versions.{suffix}")
    return module.build_typed_api(url=url, token=token)
```

Overloaded return types provide IDE completion per version:

```python title="netbox_sdk/typed_api.py"
@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.6"]) -> TypedApiV4_6: ...
@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.5"]) -> TypedApiV4_5: ...
@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.4"]) -> TypedApiV4_4: ...
@overload
def typed_api(url: str, token: str | None = None, *, netbox_version: Literal["4.3"]) -> TypedApiV4_3: ...
```

---

## HTTP Cache

`HttpCacheStore` in `netbox_sdk/http_cache.py` provides a filesystem-backed JSON cache stored under `~/.config/netbox-sdk/http-cache/`.

```mermaid
flowchart TD
    REQ["Incoming GET request"]
    KEY["build_cache_key()\nSHA-256 of base_url + method + path + query + token fingerprint"]
    LOAD["HttpCacheStore.load(key)"]
    FRESH{"Entry exists\nand is fresh?"}
    STALE{"Entry exists\nbut stale?"}
    COND["Add If-None-Match /\nIf-Modified-Since headers"]
    HTTP["Make HTTP request"]
    STATUS{"Response status"}
    S304["304 Not Modified\n→ refresh timestamps"]
    S2XX["2xx → save new entry"]
    S5XX["5xx error\n→ serve stale if within\nstale_if_error_until"]
    RETURN["Return ApiResponse\n(X-NBX-Cache header)"]

    REQ --> KEY --> LOAD --> FRESH
    FRESH -->|Yes| RETURN
    FRESH -->|No| STALE
    STALE -->|Yes| COND --> HTTP
    STALE -->|No| HTTP
    HTTP --> STATUS
    STATUS --> S304 --> RETURN
    STATUS --> S2XX --> RETURN
    STATUS --> S5XX --> RETURN
```

### Cache Key

Cache keys are SHA-256 fingerprints of the request identity — never raw credentials:

```python title="netbox_sdk/http_cache.py"
def build_cache_key(*, base_url, method, path, query, authorization) -> str:
    token_fingerprint = hashlib.sha256((authorization or "").encode()).hexdigest()
    identity = "\n".join([
        base_url.rstrip("/"),
        method.upper(),
        path,
        urlencode(sorted((query or {}).items()), doseq=True),
        token_fingerprint,
    ])
    return hashlib.sha256(identity.encode()).hexdigest()
```

### Header Precedence and Authorization Resolution

Request headers layer from three sources, lowest to highest precedence: `persistent_headers` (client-wide, e.g. the TUI's active branch or MCP's forwarded-caller override), `_scoped_headers` (a per-task `contextvars.ContextVar` set by `header_scope()`/`activate_branch()`), and the per-call `headers` argument. HTTP header names are case-insensitive but a plain `dict` is not, so `_extract_case_insensitive()` pops every case variant of a header name (`Authorization`, `authorization`, `AUTHORIZATION`, ...) from a headers dict and returns both explicit-presence state and the matching value, plus the remainder with all variants removed.

`_request_impl()` and `stream_sse()` both extract `Authorization` from each layer **separately, before merging them**, then choose the highest-precedence layer whose key was present. Presence rather than truthiness is security-critical: `headers={"Authorization": ""}` and an empty Authorization supplied through `header_scope()` intentionally select anonymous dispatch and must not fall through to the client's configured, potentially privileged token. When no layer supplies the key, the configured credential is still used; non-empty overrides behave as before. Per-layer extraction also avoids plain-`dict` iteration-order traps when different casing is used at different precedence levels.

### Cache Policies

| Request type | Fresh TTL | Stale-if-error TTL |
|---|---|---|
| GET list (e.g., `/api/dcim/devices/`) | 60 s | 300 s |
| GET detail with query | 30 s | 60 s |
| GET detail without query | 15 s | 60 s |
| Non-GET (POST/PUT/PATCH/DELETE) | Not cached | — |

Cache files use `0o600` permissions (owner read/write only) to protect token fingerprints.

### Write Invalidation and Generation Fencing

A non-GET request purges every cached entry for its path (and the containing collection path) via `HttpCacheStore.invalidate_path()`, keyed by a per-path index file rather than the full cache key — so invalidation is independent of which token, query string, or scope headers produced the cached entry. Invalidation runs after **any** completed write attempt, regardless of response status, and after an exception raised while issuing or reading the write (connection drop, timeout, malformed response). A non-2xx status is not proof the mutation didn't happen: a plugin or raw endpoint can commit the write server-side and only then fail during post-commit processing (e.g. a 500 from signal/webhook handling after the row was already written), so restricting invalidation to confirmed 2xx responses would leave that committed mutation invisible to the cache and let a verification read serve the stale pre-write entry, encouraging an unsafe duplicate retry. Invalidation failures (e.g. a cache-index filesystem error) are caught and logged as a warning rather than propagated — a cache-maintenance failure must never override a confirmed HTTP outcome, misreporting a successful write as failed or masking the real request exception behind an unrelated `OSError`. Any such failure — a lock timeout or a plain filesystem error such as a failed unlink or a read-only disk (`TimeoutError` is itself an `OSError` subclass, so one `except OSError` handler covers both) — additionally publishes a per-path cache-unavailable marker: later reads cannot report a HIT from the surviving entry and must complete a real purge before that path can be trusted or populated again.

`_invalidate_related_cache()` purges each affected path (the exact path, the collection path, and — for bulk writes — each item's own detail path) independently, catching and logging a failure on any single path rather than wrapping the whole batch in one `try`/`except`. A write can affect several distinct cache paths, and a failure purging the first one (e.g. a transient lock contention) must never abort the attempt on the rest: skipping the remaining paths after one early failure would leave them — most importantly the containing collection listing — fully cached and able to serve a fresh-looking pre-write hit immediately after the write succeeds, even though the exact path that did fail is logged and known-stale.

A GET that started before a write can still be in flight when that write's `invalidate_path()` runs. Without a fence, the GET's own `save()` call — which lands after the invalidation — could resurrect the pre-write response into a fresh cache entry, hiding a successful mutation from the next read for the rest of that entry's TTL. `HttpCacheStore` closes this race with a per-path generation counter:

- `path_generation(path)` returns the path's current generation; the client captures it immediately before issuing a cacheable GET. If coordination times out, its lock-unavailable sentinel is an explicit bypass state: the client neither loads an existing entry nor writes the live response to cache for that request.
- `invalidate_path(path)` increments the generation (and clears the key list) instead of deleting the index file outright, so a fence captured before invalidation can still be compared against it afterward.
- `save(..., path=path, expected_generation=<captured>)` re-checks the generation under the same per-path lock `invalidate_path()` uses. If the generation has moved on, the entry is still returned to satisfy the in-flight caller's own request, but neither the entry file nor the index registration is written — the response is never persisted.
- `refresh(..., path=path, expected_generation=<captured>)` applies the identical fence to a 304 revalidation. A 304 only confirms that the representation matched the ETag/Last-Modified sent from the pre-write entry; if a concurrent write invalidated the path while the conditional request was in flight, that confirmation is stale and `refresh()` must not resurrect the purged entry any more than `save()` would. When the client detects this race directly (the path's generation has moved since the conditional request began, and the response comes back 304), it discards the `If-None-Match`/`If-Modified-Since` headers and reissues the request unconditionally before persisting, rather than trusting the untrustworthy 304 at all. The generation passed to that replacement request's own fenced save is captured immediately **before** the unconditional request is issued, mirroring the capture-before-request pattern used for the very first GET — capturing it only after the replacement response arrives would leave a second race window open: a further concurrent write landing while the unconditional refetch is still in flight would otherwise be adopted as if it were the fence, letting that now-doubly-stale replacement response pass the check and get persisted as a fresh entry. The in-memory `cache_entry` reference is also dropped at that same point, before the unconditional request is issued — not after it returns. The generation mismatch already proved that entry stale, so it must not survive to be served by either of this request's own stale-if-error fallbacks (the exception handler's stale-if-error return, or `_finalize_cached_response()`'s stale-on-5xx return) if the unconditional refetch itself then raises or comes back with a server error; clearing it only after a successful refetch would leave both fallbacks able to resurrect the very entry the client just proved could no longer be trusted.

This makes the entry write and index registration atomic with respect to concurrent invalidation, closing the same-race window that a lock alone (serializing writers, not fencing readers against a write that already committed) does not.

### Action-Endpoint Cross-Resource Invalidation

Most writes only ever affect the path written and its immediate parent collection, which `_related_cache_paths()`'s default derivation (exact path + `_collection_path_for()`) already covers. NetBox's "detail action" endpoints — non-CRUD sub-paths registered per `(group, resource)` in `netbox_sdk.facade.DETAIL_ENDPOINT_SPECS`, such as `available-ips`, `available-prefixes`, and `available-vlans` — break that assumption: `POST /api/ipam/prefixes/{id}/available-ips/` creates `IPAddress` rows that live under `/api/ipam/ip-addresses/`, an entirely different collection than the prefix's own path or its parent. The default derivation would purge only `/api/ipam/prefixes/{id}/available-ips/` and `/api/ipam/prefixes/{id}/`, leaving a list cached from `/api/ipam/ip-addresses/` before the action stale until it naturally expired.

`client.py`'s module-level `_ACTION_CROSS_RESOURCE_CACHE_PATHS` maps each known mutating action's trailing path segment (`available-ips`, `available-prefixes`, `available-vlans`) to the extra collection path(s) it actually populates. `_trailing_action_name()` recognizes the general trailing shape `... / resource / numeric-id / non-numeric-action`, so core routes and plugin routes with additional leading namespaces are handled identically. `_related_cache_paths()` always steps back past both the action and ID to invalidate the resource's true collection, then adds mapped cross-resource collection(s) whenever the written action matches. Read-only actions (`napalm`, `trace`, `units`, `elevation`, `paths`) are omitted from the mapping since a GET never stales anything.

**Deliberately out of scope: aggregate/derived fields on unrelated resources.** This is a path-based cache, not a dependency-aware one. Writing a `Device` does not invalidate a cached `Site`, `Rack`, or `DeviceType` listing even though NetBox's read-only aggregates (e.g. `device_count`) on those objects would now be stale — the only cross-resource invalidation this cache performs is the explicit `_ACTION_CROSS_RESOURCE_CACHE_PATHS` mapping above, for the specific case of a detail action that is known to create rows under an entirely different collection. Extending this to every relationship that carries a derived/aggregate field would require either a full dependency graph across the bundled OpenAPI schema or unconditional store-wide invalidation on every write, both of which defeat the purpose of a filesystem-level HTTP cache for a CLI/SDK client. Callers that need a guaranteed-fresh aggregate field should not rely on a cached read for it.

The per-path index's read-modify-write is serialized by `HttpCacheStore._locked_index()`. On platforms with `fcntl` (Linux, macOS), `_acquire_flock()` polls `flock(LOCK_EX | LOCK_NB)` on the same bounded `timeout`/`poll_interval` deadline `_portable_lock` already uses, raising `TimeoutError` if the deadline passes rather than calling the unbounded blocking `flock(LOCK_EX)` form. It retries only contention errors (`EAGAIN`/`EACCES`); any other `OSError` is propagated immediately instead of being hidden behind the full timeout. The polling loops still use synchronous sleeps because same-path writers require wait-then-succeed semantics: dropping a contended save would lose that caller's key from the shared index. `NetBoxApiClient` therefore awaits every synchronous cache-store operation (`path_generation`, `load`, `invalidate_path`, unavailable marking, `refresh`, and `save`) through `asyncio.to_thread()`. A held cache lock can delay that request up to the bounded timeout without freezing unrelated coroutines, MCP callers, or health checks on the event loop. Where `fcntl` is unavailable, the portable fallback (`_portable_lock`) uses `O_CREAT | O_EXCL` atomic file creation — guaranteed exclusive-create semantics on every supported filesystem — bounded by the same kind of timeout and offloaded through the same client boundary.

### Path Canonicalization

Every fencing guarantee above depends on the cache key, the generation fence, `invalidate_path()`, and the outbound request all agreeing on the *same* request path. `NetBoxApiClient.build_url()` resolves `.`/`..` path segments via `urljoin()` before a request hits the wire, so a request through an unnormalized-but-equivalent alias (e.g. `/api/dcim/../ipam/prefixes/5/`) still lands on the canonical resource (`/api/ipam/prefixes/5/`) on the wire. `_normalize_request_path()` performs the identical dot-segment resolution and is called once, at the very top of `_request_impl()`, before any cache-related computation — so the cache key, the generation snapshot, and every `invalidate_path()` call downstream are always keyed to the same canonical path the request actually used, never the literal alias text. Without this, a write issued through such an alias would mutate the canonical resource while invalidating cache entries for the never-cached alias path, leaving the canonical cached entries (which a normal read would hit) stale and servable. `netbox_mcp/models.py`'s `CallInput._validate_path()` independently rejects decoded `.`/`..` segments outright at the MCP tool boundary, so a raw `nbx-mcp` call always targets exactly the resource its path spells out.

Dot-segment resolution alone is not enough: aiohttp builds the actual outbound request via `yarl.URL(str)` (the default, `encoded=False`), which percent-decodes every RFC 3986 *unreserved* character (`ALPHA / DIGIT / "-" / "." / "_" / "~"`) across the whole URL — not only literal or percent-encoded dot segments — before resolving any resulting `.`/`..` segments. So aliases with no dot segment at all, such as `/api/%64cim/device%73/5/` (`%64` decodes to `d`, `%73` decodes to `s`), also resolve to `/api/dcim/devices/5/` on the wire. `_normalize_request_path()` reproduces this by canonicalizing through `yarl.URL(f"http://netbox-sdk.invalid{normalized}").raw_path` — after, not instead of, the existing `posixpath.normpath()`-based repeated-slash collapsing, since yarl parsing alone does not collapse `//` runs (only `urljoin()`, used later in `build_url()`, does that). Percent-encoded path separators (`%2F` and `%5C`, case-insensitive) are different: NetBox, plugins, and reverse proxies can decode them before route matching even when yarl preserves their encoded spelling on the wire, making the literal cache path ambiguous. `_normalize_request_path()` therefore rejects them before URL construction, cache access, or network dispatch instead of guessing which deployment layer will split the segment. Other encodings, including unreserved-character aliases and encoded query values passed separately through `query`, retain their existing behavior. Without these rules, a write through an encoded alias could mutate the canonical resource while invalidating cache entries keyed to different literal text, leaving the canonical cached entry stale and servable by a verification read.

### Crash-Consistent Cache Commits

`save()` and `refresh()` register the key in the per-path index *before* writing the entry file — not the reverse. Each individual write (`_write_entry`, `_write_index_state`) is already atomic on its own (temp file + `os.replace()`), but committing an entry is inherently a two-file operation, and a crash or `OSError` between the two writes must degrade to a safe outcome. `load()` only checks whether the entry file exists — it never consults the index — while `invalidate_path()` only walks keys already registered in the index. Writing the entry first (the order used before this fix) could leave an orphan entry file on disk that `load()` would happily serve, but that `invalidate_path()` could never discover to purge on a later write — an invalidation-invisible stale hit servable indefinitely. Registering the index first means the only possible interruption leaves an index key with no matching entry file, which `load()` already treats as an ordinary cache miss.

### Crash-Safe Portable Locking

The portable fallback lock (`_portable_lock`, used on platforms without `fcntl`, notably Windows) is an `O_CREAT | O_EXCL` exclusive-create file. Unlike `flock()`, nothing releases it automatically if the holding process dies — and `path_generation()` is called unconditionally before every cacheable GET, so an abandoned lock file would otherwise block every future request through that path for the full 30 second timeout, forever, since nothing else ever removes it. Two changes make this crash-safe:

- **Ownership-safe stale-lock reclamation.** `_portable_lock` writes the creating process's PID plus a unique acquisition token into the lock file (while still accepting legacy PID-only files). A waiter checks the PID via `_pid_is_alive()` (`os.kill(pid, 0)` on POSIX; `OpenProcess`/`CloseHandle` on Windows). Reclaimers for a confirmed-dead owner's exact record serialize through an `O_CREAT | O_EXCL` claim file keyed to that record, re-read it while holding the claim, and create the replacement lock before releasing the claim. Two waiters that both observed one stale file therefore cannot unlink each other's newly created live replacement. Empty or mid-write records remain ambiguous and are left for the bounded timeout.
- **Graceful, stale-safe degradation on lock-acquisition failure.** `path_generation()` catches `TimeoutError` and returns the sentinel `_LOCK_UNAVAILABLE_GENERATION` (`-1`, which never collides with a real generation since those start at 0 and only increase) instead of propagating the exception, logging a `cache_lock_timeout` warning. The client treats that sentinel as an explicit cache-bypass state: it skips fresh-HIT lookup, conditional revalidation, and persistence for the request. `save()` and `refresh()` also return their in-memory entry unpersisted when their own lock attempt times out. If `invalidate_path()` times out after a write, it still propagates internally so the existing warning path runs, but it first creates a unique per-path unavailable marker visible to every cache-store instance sharing the root. A later `path_generation()` must successfully retry the invalidation and remove the markers it observed before it can trust that path again; a newer concurrent timeout creates a different marker and cannot be erased by the older recovery.

### Fail-Safe Purge on a Corrupted Cache Index

A per-path index file can exist but fail to parse — truncated by a crash mid-write on a filesystem without atomic-rename guarantees, hand-edited, or corrupted by an out-of-band process. `_load_index_state_or_none()` returns `None` instead of a degraded empty state when the index file exists but cannot be parsed as valid JSON with the expected shape (still returning `(0, [])`, not `None`, when the file is simply absent — the ordinary case for a path never previously written). `save()`, `refresh()`, `path_generation()`, and `invalidate_path()` all read the index through a single shared wrapper, `_load_index_state_or_purge()`, rather than calling `_load_index_state_or_none()` directly.

An earlier version of this cache degraded a corrupted index to a safe-looking empty `(0, [])` state only inside `save()`, `refresh()`, and `path_generation()`, on the reasoning that those three callers only use the index to *register or fence* new writes. That reasoning missed a race: `save()` and `refresh()` don't just fence, they also *rewrite* the per-path index file — so an ordinary write for one key on a corrupted path would "heal" the on-disk index with a fresh, valid-looking one that had silently forgotten every key the corrupted index still registered. Those forgotten keys' entry files were never purged and became permanently unreachable through the index, yet `load()` decides hits by entry-file existence alone and never consults the index — so they kept being served as fresh hits indefinitely, surviving even a later `invalidate_path()` call for that same path, since by then the index no longer listed them to purge.

`_load_index_state_or_purge()` closes this by giving all four callers the same fail-safe response to a corrupted index: on `None` from `_load_index_state_or_none()`, it calls `_purge_all_entries(corrupted_index_path)` and returns `(0, [], purged=True)` to the caller.

A subsequent fix closed a second race in that recovery path: the freshly reset generation was always `0`, and nothing distinguished it from a real, trustworthy `0` — a GET that captured `expected_generation=0` on a path that had *never* been invalidated could lose a race against a concurrent write bumping the path to generation `1`, and if the index was then found corrupted (for any unrelated reason) by the time that GET's `save()`/`refresh()` ran, the recovered `0` would match its stale captured value and let the pre-write response persist with a fresh TTL, hiding the committed mutation. `_load_index_state_or_purge()` now also calls `_mark_path_unavailable(path)` as part of recovery, and every caller (`save()`, `refresh()`, `path_generation()`) checks the `purged` flag and treats it exactly like a lock-timeout outage — `save()`/`refresh()` return their in-memory entry/refreshed-entry unpersisted, and `path_generation()` returns `_LOCK_UNAVAILABLE_GENERATION` — instead of trusting the reset `0` as a fence value. `invalidate_path()` does not need this check: it always writes a fresh, incremented generation regardless of `purged`, and the marker `_load_index_state_or_purge()` just set self-heals on the very next `path_generation()` call for that path via the existing lock-timeout bypass-and-clear flow.

An earlier version of `_purge_all_entries()` deleted every `*.json` file store-wide unconditionally — every entry file and every other path's index file, not only the corrupted path's own — reasoning that the generation-fencing invariant above made a whole-store reset safe from any of the four call sites. That reasoning missed a race of its own: resetting an unrelated, *healthy* path's generation back to 0 could let an in-flight GET for that path, which had captured generation 0 before losing a race against that path's own concurrent write bumping it to 1, have its now-stale `save()` pass the fence anyway — the rewound 0 is indistinguishable from the pre-write value the GET originally captured — and resurrect data the write had already invalidated.

`_purge_all_entries(corrupted_index_path)` now recovers *only* the corrupted path (plus any other index file that independently fails to parse mid-scan): it builds a `known_keys` set from every other, still-parseable `idx-*.json` index (leaving those indexes' own generations and entries completely untouched), deletes `corrupted_index_path` itself, and unlinks only entry files not listed by any surviving healthy index. Since `save()`/`refresh()` always register a key in its index *before* writing the entry file, an entry can only be unlisted by every valid index if the index that used to list it is the one being recovered from — so this scan can never mistakenly drop a healthy path's entry.

Secondary corrupted indexes need an additional safeguard. The scan knows only their on-disk names (`idx-<digest>.json`), not their plaintext request paths, so deleting them outright would turn a previously invalidated generation into an ordinary missing index interpreted as generation `0`. `_purge_all_entries()` now extracts the digest and publishes an `unavailable-<digest>-*.marker` before removing each secondary corrupted index. The index filename and marker prefix use the same SHA-256 of the request path, so later path-based checks discover that marker without reversing the hash. `load(..., path=path)`, `save()`, and `refresh()` reject the marked path; `path_generation()` completes `invalidate_path()` and advances the replacement index before clearing the marker. If the marker cannot be persisted, the corrupted index remains in place as the sentinel instead of being converted into a trustable missing index.

The whole scan-and-delete pass still runs under the same `_global_guard_path()` lock `save()`, `refresh()`, and `invalidate_path()` take around their own index-then-entry write pair, so it stays serialized against a concurrent writer for a *different, healthy* path the same way the original locking fix intended: that writer either finishes its whole index+entry pair before a purge can start, or only starts writing after the purge has already finished. The lock is acquired only around each method's actual write section, never around the read-then-decide phase that discovers the corruption and calls `_purge_all_entries()` in the first place — holding it there would have the corrupted path's own call deadlock against itself when it reaches its own write phase.

---

## Services Layer

`netbox_sdk/services.py` maps user-facing action names to HTTP calls, bridging the CLI and the HTTP client.

### ACTION_METHOD_MAP

| Action | HTTP Method | Path |
|---|---|---|
| `list` | GET | `list_path` |
| `get` | GET | `detail_path` (requires `--id`) |
| `create` | POST | `list_path` |
| `update` | PUT | `detail_path` (requires `--id`) |
| `patch` | PATCH | `detail_path` (requires `--id`) |
| `delete` | DELETE | `detail_path` (requires `--id`) |

### resolve_dynamic_request()

Takes a `(group, resource, action, id, query_params, payload)` tuple and returns a `ResolvedRequest(method, path, query, payload)`:

```python title="netbox_sdk/services.py"
class ResolvedRequest(BaseModel):
    method: str
    path: str
    query: dict[str, str]
    payload: dict[str, Any] | list[Any] | None
```

### run_dynamic_command()

Combines `resolve_dynamic_request()` with a `NetBoxApiClient` to execute the full request end-to-end. Used by `netbox_cli/dynamic.py` to power all `nbx <group> <resource> <action>` commands generated at startup from the OpenAPI schema.
