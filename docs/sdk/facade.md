# Facade API

`netbox_sdk` now includes an async convenience layer for common NetBox workflows.

It is feature-equivalent to the familiar PyNetBox-style navigation model, but it is
implemented on top of the existing async `NetBoxApiClient` and schema-driven SDK
internals. It is not a synchronous clone of `pynetbox`.

---

## Entry point

Use `api()` to create an `Api` object:

```python
import asyncio
from netbox_sdk import api


async def main():
    nb = api("https://netbox.example.com", token="my-token")
    version = await nb.version()
    print(version)


asyncio.run(main())
```

Top-level apps are exposed as attributes:

```python
nb.dcim
nb.ipam
nb.virtualization
nb.plugins
```

---

## CRUD and filtering

Retrieve a single object:

```python
device = await nb.dcim.devices.get(42)
if device is not None:
    print(device.name)
```

Filter a collection:

```python
devices = nb.dcim.devices.filter(site="lon", role="leaf-switch")

async for device in devices:
    print(device.name)
```

`Endpoint.all()` accepts the same filter keyword arguments as `filter()`, so the
two calls below are equivalent:

```python
async for device in nb.dcim.devices.all(role="leaf-switch"):
    ...

async for device in nb.dcim.devices.filter(role="leaf-switch"):
    ...
```

Count matching rows:

```python
count = await nb.dcim.devices.count(site="lon")
print(count)
```

Create:

```python
device = await nb.dcim.devices.create(
    name="sw-lon-01",
    site={"id": 1},
    role={"id": 2},
    device_type={"id": 3},
)
print(device.id)
```

Bulk update:

```python
result = await nb.dcim.devices.update(
    [
        {"id": 10, "name": "sw-lon-10"},
        {"id": 11, "name": "sw-lon-11"},
    ]
)
```

Bulk delete:

```python
await nb.dcim.devices.delete([10, 11, 12])
```

---

## Record helpers

Objects returned by the facade are lightweight records with endpoint context.

Refresh full details:

```python
device = await nb.dcim.devices.get(42)
await device.full_details()
print(device.serial)
```

Save only changed fields:

```python
device.name = "sw-lon-01-renamed"
print(device.updates())  # {"name": "sw-lon-01-renamed"}
await device.save()
```

Delete a single record:

```python
await device.delete()
```

---

## Detail endpoints

The facade exposes common NetBox subresources directly from records.

Available IPs and prefixes:

```python
prefix = await nb.ipam.prefixes.get(123)

available_ips = await prefix.available_ips.list()
new_ip = await prefix.available_ips.create({})

new_prefix = await prefix.available_prefixes.create({"prefix_length": 28})
```

Rack elevation:

```python
rack = await nb.dcim.racks.get(5)

units = await rack.elevation.list()
svg = await rack.elevation.list(render="svg")
```

NAPALM and render-config:

```python
device = await nb.dcim.devices.get(42)
facts = await device.napalm.list(method="get_facts")
rendered = await device.render_config.create()
```

---

## Trace and path helpers

Traceable records expose `trace()`:

```python
interface = await nb.dcim.interfaces.get(100)
trace = await interface.trace()
```

Path-aware records expose `paths()`:

```python
termination = await nb.circuits.circuit_terminations.get(7)
paths = await termination.paths()
```

---

## Plugins and app config

Installed plugin metadata:

```python
plugins = await nb.plugins.installed_plugins()
```

Plugin resources:

```python
olts = nb.plugins.gpon.olts.filter(status="active")
async for olt in olts:
    print(olt.name)
```

Per-app config:

```python
user_config = await nb.users.config()
```

---

## Branch activation

Branch-scoped requests can be made with `activate_branch()`:

```python
branch = type("Branch", (), {"schema_id": "feature-x"})()

with nb.activate_branch(branch):
    device = await nb.dcim.devices.get(42)
```

This sets `X-NetBox-Branch` on requests made within the context.

---

## Strict filters

Enable OpenAPI-backed filter validation at API construction time:

```python
nb = api(
    "https://netbox.example.com",
    token="my-token",
    strict_filters=True,
)
```

Or override per query:

```python
devices = nb.dcim.devices.filter(site="lon", strict_filters=True)
```

Unknown filters raise `ParameterValidationError`.

---

## Pagination

The facade transparently paginates list iteration. NetBox 4.6 introduced cursor-based
pagination over a `start=<pk>&limit=<n>` query, which is significantly faster than
offset-based pagination on large result sets. The SDK auto-detects the running NetBox
version and selects the right strategy:

- NetBox `>= 4.6`: cursor mode (default).
- NetBox `< 4.6`: offset mode (legacy).

### Parameter matrix

Every paginated method accepts the full set of NetBox pagination arguments plus
arbitrary filter keywords:

| Method | `limit` | `offset` | `start` | `mode` | filter `**kwargs` |
|---|:---:|:---:|:---:|:---:|:---:|
| `Endpoint.all(...)` | yes | yes | yes | yes | yes |
| `Endpoint.filter(...)` | yes | yes | yes | yes | yes |
| `Endpoint.get(...)` | — | — | — | — | yes |
| `Endpoint.count(...)` | — | — | — | — | yes |

`mode` accepts `"cursor"`, `"offset"`, or `"auto"`. `start` and `offset` are mutually
exclusive; passing both raises `ValueError`. `ordering` is rejected in cursor mode
(NetBox enforces this server-side).

### Cursor mode (default)

```python
nb = api("https://netbox.example.com", token="my-token")

# Cursor by default on NetBox >= 4.6 (filters and pagination compose freely):
async for device in nb.dcim.devices.all(role="leaf-switch", limit=100):
    print(device.id)

# Seed an explicit cursor:
async for device in nb.dcim.devices.all(limit=100, start=0):
    print(device.id)
```

### Using the legacy offset method

The legacy offset paginator is fully supported. Force it for the whole client or
for a single query:

```python
# Whole client:
nb = api("https://netbox.example.com", token="my-token", pagination_mode="offset")

# Per query:
async for device in nb.dcim.devices.all(mode="offset", limit=100):
    print(device.id)

devices = nb.dcim.devices.filter(role="leaf-switch", mode="offset")
```

The environment variable `NETBOX_SDK_PAGINATION_MODE` (`cursor` / `offset` / `auto`)
overrides the constructor default, useful when bisecting issues against a specific
NetBox release. In cursor mode the server returns `count: null` for performance, so
`Endpoint.count()` issues an explicit offset-mode probe to obtain the total —
`count()` works regardless of the configured mode.

---

## Notes

- The facade is async-first. Use it inside `async def` functions.
- It reuses the lower-level client; `NetBoxApiClient` remains available when you want direct request control.
- The implementation is intentionally explicit. It does not try to reproduce PyNetBox's synchronous or implicit lazy-fetch behavior exactly.
