# NetBox SDK

`netbox_sdk` is a standalone Python library for connecting to NetBox over its REST API. It is the shared core used by both the CLI and the TUI, but it can also be imported independently in any Python project.

The SDK exposes three layers:

- `NetBoxApiClient` for low-level async request control
- `api()` / `Api` for a higher-level async facade with PyNetBox-style workflows
- `typed_api()` for a versioned typed client backed by committed Pydantic models

## Modules

| Module | Responsibility |
|---|---|
| `netbox_sdk.config` | Config model, profile persistence, auth header construction |
| `netbox_sdk.client` | Async HTTP client and connection probe |
| `netbox_sdk.facade` | Async convenience API for apps, endpoints, records, and detail routes |
| `netbox_sdk.typed_api` | Versioned typed client factory |
| `netbox_sdk.models` | Committed generated Pydantic models for supported NetBox releases |
| `netbox_sdk.typed_versions` | Committed generated typed endpoint bindings |
| `netbox_sdk.http_cache` | Filesystem cache with TTL/stale-if-error support |
| `netbox_sdk.schema` | OpenAPI schema loading and indexing |
| `netbox_sdk.services` | Dynamic request resolution |
| `netbox_sdk.plugin_discovery` | Runtime plugin/custom-object API discovery |

## Installation

```bash
pip install netbox-sdk
```

You do not need the optional CLI or TUI extras to use `netbox_sdk` as a Python
dependency.

## Quick start

```python
import asyncio
from netbox_sdk import api


async def main():
    nb = api("https://netbox.example.com", token="your-token")

    device = await nb.dcim.devices.get(42)
    if device is not None:
        print(device.name)

asyncio.run(main())
```

If you want raw HTTP control instead of the facade, use `NetBoxApiClient` directly.

### Schema compatibility contract

`api()` is a synchronous factory, so it does not contact the server while it is
being constructed. If `schema=` is omitted, construction starts with the newest
stable bundled contract (currently NetBox 4.7), then the first
schema-dependent request detects the connected release and replaces that
provisional index. Detection and live-schema failures propagate instead of
silently retaining the default contract. For a known older server, you can
bypass detection and pin its schema explicitly:

```python
from netbox_sdk import api, build_schema_index

nb = api(
    "https://netbox.example.com",
    token="your-token",
    schema=build_schema_index(version="4.6"),
)
```

For an unpinned server, omit `schema=` and let the first request detect every
supported release line, or use `await async_api(...)` when detection must finish
before the facade is returned. With `strict_filters` enabled, deferred
validation runs after detection; an unknown-filter error names the loaded
schema and points to the available selection paths because the rejection is
local and no request reached NetBox.

## Plugins and custom objects

Use `async_api()` when you want eager schema selection and runtime-resource
enrichment. It discovers plugin REST collections under
`/api/plugins/` and public ObjectType resources advertised by
`/api/core/object-types/`.

```python
from netbox_sdk import async_api

nb = await async_api("https://netbox.example.com", token="your-token")
widgets = await nb.plugins.custom.widgets.all().to_list()
```

The SDK supports plugin/custom objects that expose standard REST list/detail
endpoints. Private models or plugin data without a REST endpoint are skipped.

## Typed SDK

Use `typed_api()` when you want request and response validation plus IDE-visible
endpoint models.

```python
from netbox_sdk import typed_api

nb = typed_api(
    "https://netbox.example.com",
    token="your-token",
    netbox_version="4.5",
)
```

Supported release lines:

- `4.7` (stable, default; official `v4.7.0` GA schema)
- `4.6`
- `4.5`
- `4.4`
- `4.3`

Patch versions normalize to the matching release line, for example `4.5.5` maps
to `4.5`.
