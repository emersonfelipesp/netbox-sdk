# Error Handling

---

## RequestError

`request()` does **not** raise on non-2xx status codes by default — it returns an `ApiResponse` with the status code. Inspect the status yourself:

```python
response = await client.request("GET", "/api/dcim/devices/99/")

if response.status == 404:
    print("Device not found")
elif response.status == 403:
    print("Forbidden — check your token")
elif response.status >= 500:
    print(f"Server error: {response.text}")
elif response.status == 200:
    device = response.json()
```

`RequestError` is raised only by `get_version()`:

```python
from netbox_sdk import RequestError

try:
    version = await client.get_version()
except RequestError as exc:
    print(f"HTTP {exc.response.status}: {exc.response.text}")
```

The facade layer raises `RequestError` for failed endpoint operations such as
`await nb.dcim.devices.get(1)` when the response is not a handled success case.

---

## Facade-specific exceptions

The higher-level facade adds a few explicit exceptions for common NetBox SDK workflows.

### ParameterValidationError

Raised when strict filter validation is enabled and a filter name is not present
in the OpenAPI schema:

```python
from netbox_sdk import ParameterValidationError, api

nb = api("https://netbox.example.com", token="tok", strict_filters=True)

try:
    nb.dcim.devices.filter(not_a_real_filter="value")
except ParameterValidationError as exc:
    print(exc)
```

### AllocationError

Raised for allocation-style detail endpoints when NetBox returns HTTP 409:

```python
from netbox_sdk import AllocationError

prefix = await nb.ipam.prefixes.get(123)

try:
    await prefix.available_prefixes.create({"prefix_length": 28})
except AllocationError as exc:
    print(exc)
```

### ContentError

Raised when the facade expects JSON but the server returns invalid content:

```python
from netbox_sdk import ContentError

try:
    plugins = await nb.plugins.installed_plugins()
except ContentError:
    print("NetBox returned invalid JSON")
```

---

## ConnectionProbe

Use `probe_connection()` before any API calls to validate connectivity and surface human-readable errors:

```python
probe = await client.probe_connection()

if not probe.ok:
    # Common cases:
    # probe.status == 0  → network unreachable (DNS, TCP, TLS failure)
    # probe.status == 404 → base_url points to wrong path
    # probe.status == 401 → auth rejected (invalid token)
    print(f"Cannot reach NetBox (HTTP {probe.status}): {probe.error}")
    return

print(f"NetBox API version: {probe.version}")
```

`ConnectionProbe` fields:

| Field | Type | Meaning |
|-------|------|---------|
| `ok` | `bool` | `True` if NetBox is reachable (status < 400, or 403) |
| `status` | `int` | HTTP status code; `0` on network-level failure |
| `version` | `str` | Value of the `API-Version` response header |
| `error` | `str \| None` | Human-readable error, or `None` if `ok` is `True` |

Note: 403 counts as `ok=True` because it means the URL is valid — only the token is wrong.

---

## Network errors

Network-level failures (DNS failure, TCP timeout, TLS error) are raised as exceptions from `request()`. The client catches them internally when a stale cache entry exists; otherwise they propagate:

```python
import aiohttp

try:
    response = await client.request("GET", "/api/dcim/devices/")
except aiohttp.ClientConnectorError as exc:
    print(f"Cannot connect: {exc}")
except TimeoutError:
    print("Request timed out")
```

If a stale cache entry exists for the failed request, `request()` returns the stale response with `X-NBX-Cache: STALE` instead of raising.

---

## Timeout configuration

The default timeout is 30 seconds. Adjust per connection:

```python
from netbox_sdk import Config

cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v1",
    token_secret="tok",
    timeout=10.0,   # 10 second timeout
)
```

---

## Missing configuration

Check completeness before making calls:

```python
from netbox_sdk.config import is_runtime_config_complete

cfg = Config(base_url="https://nb.example.com", token_version="v2", token_secret="s")
if not is_runtime_config_complete(cfg):
    # For v2: missing token_key
    # For v1: missing token_secret
    # For both: missing base_url
    raise RuntimeError("Incomplete configuration")
```

`build_url()` raises `RuntimeError("NetBox base URL is not configured")` if `base_url` is `None`.

---

## Schema resolution errors

```python
from netbox_sdk.services import resolve_dynamic_request

try:
    req = resolve_dynamic_request(idx, "dcim", "typo", "list", ...)
except ValueError as exc:
    print(exc)   # "Resource not found: dcim/typo"

try:
    req = resolve_dynamic_request(idx, "dcim", "devices", "get", object_id=None, ...)
except ValueError as exc:
    print(exc)   # "Action 'get' requires --id"
```

---

## JSON parse errors

`ApiResponse.json()` raises `json.JSONDecodeError` if the response body is not valid JSON. Always check the status code first — error responses (4xx/5xx) are sometimes HTML:

```python
response = await client.request("GET", "/api/dcim/devices/")
if response.status == 200:
    data = response.json()
else:
    print(f"Error {response.status}: {response.text[:200]}")
```

The facade wraps this case as `ContentError` when a higher-level operation
requires JSON decoding.

---

## Typed SDK validation errors

The typed client adds explicit Pydantic-backed validation failures.

### TypedRequestValidationError

Raised before HTTP when the request body does not match the versioned request
model for the selected NetBox release line.

```python
from netbox_sdk import TypedRequestValidationError, typed_api

nb = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

try:
    await nb.ipam.prefixes.available_ips.create(7, body=[{"prefix_length": "invalid"}])
except TypedRequestValidationError as exc:
    print(exc)
```

### TypedResponseValidationError

Raised after HTTP when NetBox returns JSON that does not match the expected
typed response model.

```python
from netbox_sdk import TypedResponseValidationError

try:
    await nb.dcim.devices.get(42)
except TypedResponseValidationError as exc:
    print(exc)
```
