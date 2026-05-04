# Pagination and Filtering

The mock server returns NetBox-style paginated list responses and supports query parameter filtering on any field.

## Pagination envelope

Every list response wraps results in the standard NetBox envelope:

```json
{
  "count": 50,
  "next": "http://testserver/api/dcim/sites/?limit=10&offset=10",
  "previous": null,
  "results": [...]
}
```

| Field | Description |
|---|---|
| `count` | Total number of matching objects (across all pages) |
| `next` | URL of the next page, or `null` on the last page |
| `previous` | URL of the previous page, or `null` on the first page |
| `results` | Objects in the current page window |

## Limit and offset

Use `limit` and `offset` query parameters to page through results:

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
client.post("/mock/reset")

# Seed 10 sites
client.post(
    "/api/dcim/sites/",
    json=[{"name": f"Site-{i}", "slug": f"site-{i}"} for i in range(10)],
)

# First page
resp = client.get("/api/dcim/sites/?limit=4&offset=0")
data = resp.json()
assert data["count"] == 10
assert len(data["results"]) == 4
assert data["next"] is not None
assert data["previous"] is None

# Second page
resp = client.get("/api/dcim/sites/?limit=4&offset=4")
data = resp.json()
assert len(data["results"]) == 4
assert data["next"] is not None
assert data["previous"] is not None

# Last page
resp = client.get("/api/dcim/sites/?limit=4&offset=8")
data = resp.json()
assert len(data["results"]) == 2
assert data["next"] is None
assert data["previous"] is not None
```

When `limit` is not specified, all results are returned in a single page.

## Query parameter filtering

Pass any field name as a query parameter to filter results. The filter performs a case-sensitive equality match on string fields.

```python
client.post(
    "/api/dcim/sites/",
    json=[
        {"name": "Alpha", "slug": "alpha"},
        {"name": "Beta", "slug": "beta"},
        {"name": "Gamma", "slug": "gamma"},
    ],
)

# Filter by name
resp = client.get("/api/dcim/sites/?name=Alpha")
assert resp.json()["count"] == 1
assert resp.json()["results"][0]["name"] == "Alpha"

# No matches
resp = client.get("/api/dcim/sites/?name=DoesNotExist")
assert resp.json()["count"] == 0
assert resp.json()["results"] == []
```

## Combining pagination and filtering

Filtering and pagination work together. `count` reflects the filtered total:

```python
# Create 6 VLANs with alternating names
client.post(
    "/api/ipam/vlans/",
    json=[
        {"name": "MGMT", "vid": i * 10} for i in range(3)
    ] + [
        {"name": "PROD", "vid": 100 + i * 10} for i in range(3)
    ],
)

resp = client.get("/api/ipam/vlans/?name=MGMT&limit=2")
data = resp.json()
assert data["count"] == 3       # 3 MGMT VLANs total
assert len(data["results"]) == 2  # 2 per page
```
