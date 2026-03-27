# NetBox SDK

`netbox_sdk` is a standalone Python library for connecting to NetBox over its REST API. It is the shared core used by both the CLI and the TUI, but it can also be imported independently in any Python project.

## Modules

| Module | Responsibility |
|---|---|
| `netbox_sdk.config` | Config model, profile persistence, auth header construction |
| `netbox_sdk.client` | Async HTTP client and connection probe |
| `netbox_sdk.http_cache` | Filesystem cache with TTL/stale-if-error support |
| `netbox_sdk.schema` | OpenAPI schema loading and indexing |
| `netbox_sdk.services` | Dynamic request resolution |
| `netbox_sdk.plugin_discovery` | Runtime plugin API discovery |

## Installation

```bash
pip install netbox-sdk
```

## Quick start

```python
import asyncio
from netbox_sdk import Config, NetBoxApiClient

cfg = Config(
    base_url="https://netbox.example.com",
    token_version="v2",
    token_key="your-token-key",
    token_secret="your-token-secret",
)

async def main():
    client = NetBoxApiClient(cfg)
    probe = await client.probe_connection()
    if not probe.ok:
        print(probe.error)
        return
    response = await client.request("GET", "/api/dcim/devices/", query={"limit": 5})
    print(response.json())

asyncio.run(main())
```
