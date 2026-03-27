# NetBox SDK

The `sdk` package is a standalone Python library for connecting to any NetBox instance over its REST API. It ships as part of the `netbox-console` repository but has **zero dependency on the CLI or TUI layers** — it can be imported and used independently in any Python project.

---

## What it provides

| Module | Responsibility |
|--------|---------------|
| `sdk.config` | Connection config model, profile persistence, auth header construction |
| `sdk.client` | Async HTTP client (`NetBoxApiClient`) with caching and token fallback |
| `sdk.http_cache` | Filesystem response cache with TTL and stale-if-error |
| `sdk.schema` | OpenAPI schema indexing — groups, resources, operations, filter params |
| `sdk.services` | Request resolution: (group, resource, action) → (method, path, payload) |
| `sdk.plugin_discovery` | Runtime discovery of plugin API endpoints |

---

## Installation

The SDK is included when you install `netbox-console`:

```bash
pip install netbox-console
```

Or use it from a local checkout:

```bash
# inside the netbox-cli repo
python -c "from sdk import NetBoxApiClient; print('ok')"
```

---

## Quick start

```python
import asyncio
from sdk import Config, NetBoxApiClient

cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v2",
    token_key="your-token-key",
    token_secret="your-token-secret",
)

async def main():
    client = NetBoxApiClient(cfg)

    # Check connectivity
    probe = await client.probe_connection()
    if not probe.ok:
        print(f"Connection failed: {probe.error}")
        return

    print(f"Connected — NetBox API version {probe.version}")

    # List devices
    response = await client.request("GET", "/api/dcim/devices/", query={"limit": 5})
    data = response.json()
    for device in data["results"]:
        print(device["name"])

asyncio.run(main())
```

---

## Environment variable configuration

If you prefer not to store credentials in code:

```bash
export NETBOX_URL=https://netbox.example.com
export NETBOX_TOKEN_KEY=your-key-id
export NETBOX_TOKEN_SECRET=your-secret
```

```python
from sdk.config import load_config

cfg = load_config()   # reads env vars automatically
```

---

## Next steps

- [Authentication](authentication.md) — token versions, profiles, environment variables
- [Making Requests](making-requests.md) — all HTTP methods, pagination, filtering, GraphQL
- [Schema Indexing](schema.md) — OpenAPI-driven resource discovery
- [Error Handling](error-handling.md) — `RequestError`, `ConnectionProbe`, network failures
