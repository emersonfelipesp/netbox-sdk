# CRUD Operations

The mock server supports the full NetBox CRUD lifecycle: create, read, update, and delete. This page walks through each operation using `fastapi.testclient.TestClient`.

## Setup

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
```

For tests that need a clean state before each run, call the reset endpoint:

```python
client.post("/mock/reset")
```

## Create (POST)

`POST` to a list endpoint returns the created object with an auto-assigned integer `id` and status `201`.

```python
resp = client.post(
    "/api/dcim/sites/",
    json={"name": "London HQ", "slug": "london-hq"},
)
assert resp.status_code == 201
site = resp.json()
print(site["id"])    # auto-assigned integer
print(site["name"])  # "London HQ"
```

IDs are per-collection and always monotonically increasing.

## Read (GET)

### List all objects

```python
resp = client.get("/api/dcim/sites/")
assert resp.status_code == 200
body = resp.json()
print(body["count"])    # total matching objects
print(body["results"])  # list of objects
```

All list responses use the NetBox pagination envelope:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [...]
}
```

### Get a single object

```python
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 200
print(resp.json()["name"])
```

### Auto-seeding unknown IDs

Fetching an ID that was never created returns a deterministically generated stub rather than 404:

```python
resp = client.get("/api/dcim/sites/9999/")
assert resp.status_code == 200  # auto-seeded
assert resp.json()["id"] == 9999
```

This is useful when testing code that follows nested foreign-key IDs returned by other endpoints.

## Update (PUT / PATCH)

### Full replacement (PUT)

```python
resp = client.put(
    f"/api/dcim/sites/{site_id}/",
    json={"name": "Updated Name", "slug": "updated-name"},
)
assert resp.status_code == 200
assert resp.json()["name"] == "Updated Name"
```

### Partial update (PATCH)

```python
resp = client.patch(
    f"/api/dcim/sites/{site_id}/",
    json={"name": "Patched Name"},
)
assert resp.status_code == 200
assert resp.json()["name"] == "Patched Name"
```

PATCH merges the given fields into the existing object — omitted fields retain their current values.

## Delete (DELETE)

```python
resp = client.delete(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 204
```

After deletion, GET requests to the same URL return 404:

```python
resp = client.get(f"/api/dcim/sites/{site_id}/")
assert resp.status_code == 404
```

## Complete lifecycle example

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()

with TestClient(app) as client:
    client.post("/mock/reset")

    # Create
    site = client.post(
        "/api/dcim/sites/",
        json={"name": "Test Site", "slug": "test-site"},
    ).json()
    site_id = site["id"]

    # Read
    assert client.get(f"/api/dcim/sites/{site_id}/").json()["name"] == "Test Site"
    assert client.get("/api/dcim/sites/").json()["count"] == 1

    # Update
    client.patch(f"/api/dcim/sites/{site_id}/", json={"name": "Renamed"})
    assert client.get(f"/api/dcim/sites/{site_id}/").json()["name"] == "Renamed"

    # Delete
    assert client.delete(f"/api/dcim/sites/{site_id}/").status_code == 204
    assert client.get(f"/api/dcim/sites/{site_id}/").status_code == 404
    assert client.get("/api/dcim/sites/").json()["count"] == 0
```
