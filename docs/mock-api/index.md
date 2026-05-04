# Mock API

`netbox_sdk.mock` is a self-contained FastAPI server that dynamically generates all NetBox REST API endpoints from the bundled OpenAPI specs. Every route is backed by an in-memory store so you can run full CRUD workflows without a live NetBox instance.

## Use cases

- Offline SDK development
- CI test suites that don't need a real NetBox container
- Integration testing with fast, deterministic state reset
- Examples, demos, and tutorials

## Installation

The mock server depends on FastAPI and optionally uvicorn (for standalone use). Install the `mock` extra:

```bash
pip install 'netbox-sdk[mock]'
```

Or for development with the full environment:

```bash
uv sync --dev --extra mock
```

## Quick start

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)

# Create a site
resp = client.post("/api/dcim/sites/", json={"name": "London HQ", "slug": "london-hq"})
assert resp.status_code == 201
site_id = resp.json()["id"]

# Fetch it back
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.json()["name"] == "London HQ"

# Delete it
resp = client.delete(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 204
```

## Modules

| Module | Responsibility |
|---|---|
| `netbox_sdk.mock.app` | `create_mock_app()` factory, utility routes, app assembly |
| `netbox_sdk.mock.routes` | Dynamic route registration from OpenAPI spec |
| `netbox_sdk.mock.state` | `ThreadSafeMockStore` in-memory CRUD store |
| `netbox_sdk.mock.schema_helpers` | `$ref` resolution, sample value generation |
| `netbox_sdk.mock.netbox_fields` | NetBox-specific semantic mock field values |
| `netbox_sdk.mock.loader` | Custom mock data loading from JSON/YAML |

## Utility endpoints

In addition to all NetBox API paths, the mock server exposes:

| Endpoint | Method | Description |
|---|---|---|
| `/health` | `GET` | Returns `{"status": "ready"}` |
| `/api/status/` | `GET` | Mock NetBox status with version info |
| `/mock/reset` | `POST` | Clears all in-memory state |
| `/mock/state` | `GET` | Reports route count and store statistics |

## NetBox version

The mock server defaults to the latest supported NetBox release. Override it with:

```bash
NETBOX_MOCK_VERSION=4.3 python your_script.py
```

Or pass the version directly:

```python
app = create_mock_app(version="4.3")
```

Supported values: `4.3`, `4.4`, `4.5`, `4.6`.
