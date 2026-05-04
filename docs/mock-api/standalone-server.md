# Standalone Server

The mock server can run as a standalone HTTP service using uvicorn. This is useful for manual API exploration, integration with non-Python clients, and local development against the NetBox API without a real NetBox instance.

## Installation

The standalone server requires uvicorn. Install the `mock` extra:

```bash
pip install 'netbox-sdk[mock]'
```

## Starting the server

```bash
nbx-mock
```

The server starts on `http://0.0.0.0:8001` by default and logs all requests to the console.

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `NETBOX_MOCK_VERSION` | `4.5` | NetBox OpenAPI version to generate routes from |
| `NETBOX_MOCK_HOST` | `0.0.0.0` | Bind address |
| `NETBOX_MOCK_PORT` | `8001` | Listen port |
| `NETBOX_MOCK_DATA_PATH` | _(unset)_ | Path to a JSON or YAML file with seed data |

Example:

```bash
NETBOX_MOCK_VERSION=4.3 NETBOX_MOCK_PORT=9000 nbx-mock
```

## Exploring the API

Once running, the interactive API docs are available at:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

All ~1100 NetBox endpoints are listed and executable from the browser.

## Using with curl

```bash
# Create a site
curl -s -X POST http://localhost:8001/api/dcim/sites/ \
  -H "Content-Type: application/json" \
  -d '{"name": "London HQ", "slug": "london-hq"}' | python3 -m json.tool

# List sites
curl -s http://localhost:8001/api/dcim/sites/ | python3 -m json.tool

# Get a specific site (replace 1 with the returned id)
curl -s http://localhost:8001/api/dcim/sites/1/ | python3 -m json.tool

# Update a site
curl -s -X PATCH http://localhost:8001/api/dcim/sites/1/ \
  -H "Content-Type: application/json" \
  -d '{"name": "London DC"}' | python3 -m json.tool

# Delete a site
curl -s -X DELETE http://localhost:8001/api/dcim/sites/1/ -v

# Reset all state
curl -s -X POST http://localhost:8001/mock/reset

# Check server health
curl -s http://localhost:8001/health
```

## Using with the NetBox SDK

Point `NetBoxApiClient` at the mock server:

```python
import asyncio
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import NetBoxConfig


async def main() -> None:
    config = NetBoxConfig(
        url="http://localhost:8001",
        token="mock-token",  # any string is accepted
    )
    client = NetBoxApiClient(config)

    resp = await client.get("/api/dcim/sites/")
    data = await resp.json()
    print(f"Sites: {data['count']}")

    await client.close()


asyncio.run(main())
```

## Programmatic startup

Use `create_mock_app()` with uvicorn directly in Python:

```python
import uvicorn
from netbox_sdk.mock import create_mock_app

app = create_mock_app(version="4.5")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
```

## Seed data

Pre-populate the server with data by providing a JSON file:

```json
{
  "/api/dcim/sites/": [
    {"name": "London HQ", "slug": "london-hq"},
    {"name": "New York DC", "slug": "new-york-dc"}
  ],
  "/api/ipam/vlans/": [
    {"name": "Management", "vid": 1},
    {"name": "Production", "vid": 100}
  ]
}
```

Then start the server with:

```bash
NETBOX_MOCK_DATA_PATH=/path/to/seed.json nbx-mock
```
