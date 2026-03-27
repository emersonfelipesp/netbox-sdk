# Making Requests

All NetBox API calls go through `NetBoxApiClient.request()`. The client is async — use it inside an `asyncio` event loop or an `async def` function.

---

## Basic usage

```python
from netbox_sdk import Config, NetBoxApiClient

cfg = Config(base_url="https://netbox.example.com", token_version="v1", token_secret="mytoken")
client = NetBoxApiClient(cfg)
```

### GET — list resources

```python
response = await client.request("GET", "/api/dcim/devices/")
data = response.json()

print(data["count"])    # total number of results
print(data["results"])  # list of device objects
```

### GET — filter results

```python
response = await client.request(
    "GET",
    "/api/dcim/devices/",
    query={"site": "lon", "role": "leaf-switch", "limit": "50"},
)
```

### GET — retrieve single object

```python
response = await client.request("GET", "/api/dcim/devices/42/")
device = response.json()
print(device["name"])
```

### POST — create

```python
response = await client.request(
    "POST",
    "/api/dcim/devices/",
    payload={
        "name": "sw-lon-01",
        "device_type": {"id": 3},
        "site": {"id": 1},
        "role": {"id": 2},
    },
)
if response.status == 201:
    new_device = response.json()
    print(f"Created device ID {new_device['id']}")
```

### PUT — full update

```python
response = await client.request(
    "PUT",
    "/api/dcim/devices/42/",
    payload={
        "name": "sw-lon-01-renamed",
        "device_type": {"id": 3},
        "site": {"id": 1},
        "role": {"id": 2},
    },
)
```

### PATCH — partial update

```python
response = await client.request(
    "PATCH",
    "/api/dcim/devices/42/",
    payload={"name": "sw-lon-01-renamed"},
)
```

### DELETE

```python
response = await client.request("DELETE", "/api/dcim/devices/42/")
if response.status == 204:
    print("Deleted")
```

---

## Response object

`request()` always returns `ApiResponse`:

```python
class ApiResponse(BaseModel):
    status: int               # HTTP status code
    text: str                 # raw response body
    headers: dict[str, str]   # response headers

    def json(self) -> Any: ...  # parse text as JSON
```

Check the status code before parsing:

```python
response = await client.request("GET", "/api/dcim/devices/99/")
if response.status == 404:
    print("Device not found")
elif response.status == 200:
    device = response.json()
```

---

## Pagination

NetBox list endpoints return paginated results. Iterate pages manually:

```python
async def list_all_devices(client: NetBoxApiClient) -> list[dict]:
    results = []
    offset = 0
    limit = 100
    while True:
        response = await client.request(
            "GET",
            "/api/dcim/devices/",
            query={"limit": str(limit), "offset": str(offset)},
        )
        data = response.json()
        results.extend(data["results"])
        if not data.get("next"):
            break
        offset += limit
    return results
```

---

## GraphQL

```python
query = """
{
  device_list(site: "lon") {
    id
    name
    device_type { model }
    primary_ip4 { address }
  }
}
"""
response = await client.graphql(query)
data = response.json()["data"]["device_list"]
```

With variables:

```python
query = "query($id: Int!) { device(id: $id) { name status } }"
response = await client.graphql(query, variables={"id": 42})
```

---

## Connection health check

Before making API calls, verify connectivity:

```python
from netbox_sdk import ConnectionProbe

probe = await client.probe_connection()

if probe.ok:
    print(f"Connected — NetBox API {probe.version}")
else:
    print(f"Failed (HTTP {probe.status}): {probe.error}")
```

`probe_connection()` returns `ok=True` for any reachable status below 400, or 403 (which means the URL is valid but the token is wrong — still reachable).

---

## HTTP caching

GET requests to `/api/...` paths are automatically cached to disk (`~/.config/netbox-cli/http-cache/`). The `X-NBX-Cache` response header shows the cache outcome:

| Value | Meaning |
|-------|---------|
| `MISS` | First fetch, stored to cache |
| `HIT` | Served from fresh cache |
| `REVALIDATED` | Server returned 304, cache TTL extended |
| `STALE` | Network error; stale data served |

Tune the cache policy:

```python
from netbox_sdk.http_cache import CachePolicy, HttpCacheStore
from netbox_sdk.config import cache_dir

# Default: 60s fresh, 300s stale-if-error for list endpoints
store = HttpCacheStore(cache_dir())
```

POST/PUT/PATCH/DELETE requests are **never cached**.

---

## Schema-driven requests

Use `netbox_sdk.services` to resolve action names to HTTP calls:

```python
from netbox_sdk import build_schema_index
from netbox_sdk.services import resolve_dynamic_request, run_dynamic_command

idx = build_schema_index()

# Resolve to a ResolvedRequest
req = resolve_dynamic_request(
    idx, "dcim", "devices", "list",
    object_id=None, query={"site": "lon"}, payload=None,
)
# req.method == "GET", req.path == "/api/dcim/devices/", req.query == {"site": "lon"}

# Or run it directly
response = await run_dynamic_command(
    client, idx, "dcim", "devices", "list",
    object_id=None,
    query_pairs=["site=lon"],
    body_json=None,
    body_file=None,
)
```

Supported actions: `list`, `get`, `create`, `update`, `patch`, `delete`.
