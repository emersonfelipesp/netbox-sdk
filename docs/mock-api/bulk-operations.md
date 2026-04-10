# Bulk Operations

NetBox list endpoints accept arrays in request bodies for POST, PUT, PATCH, and DELETE — allowing multiple objects to be created, updated, or deleted in a single request. The mock server implements all four bulk operations.

## Bulk create (POST array)

Pass a JSON array to any list endpoint. The response is a list of created objects with auto-assigned IDs.

```python
from fastapi.testclient import TestClient
from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)
client.post("/mock/reset")

resp = client.post(
    "/api/ipam/vlans/",
    json=[
        {"name": "Management", "vid": 1},
        {"name": "Production", "vid": 100},
        {"name": "DMZ", "vid": 200},
    ],
)
assert resp.status_code == 201
vlans = resp.json()
assert isinstance(vlans, list)
assert len(vlans) == 3

vlan_ids = [v["id"] for v in vlans]
```

The list count reflects all created objects:

```python
assert client.get("/api/ipam/vlans/").json()["count"] == 3
```

## Bulk update (PUT array)

Pass an array where each item includes its `id` field. All listed objects are fully replaced.

```python
resp = client.put(
    "/api/ipam/vlans/",
    json=[
        {"id": vlan_ids[0], "name": "MGMT", "vid": 1},
        {"id": vlan_ids[1], "name": "PROD", "vid": 100},
    ],
)
assert resp.status_code == 200
updated = resp.json()
assert updated[0]["name"] == "MGMT"
assert updated[1]["name"] == "PROD"
```

## Bulk patch (PATCH array)

Each item must include its `id`. Only the fields you provide are updated.

```python
resp = client.patch(
    "/api/ipam/vlans/",
    json=[
        {"id": vlan_ids[2], "name": "DMZ-Updated"},
    ],
)
assert resp.status_code == 200
assert resp.json()[0]["name"] == "DMZ-Updated"
```

## Bulk delete (DELETE array)

!!! note
    Use `client.request("DELETE", path, json=[...])` — Starlette's `client.delete()` method does not accept a `json` parameter.

```python
resp = client.request(
    "DELETE",
    "/api/ipam/vlans/",
    json=[{"id": vlan_ids[0]}, {"id": vlan_ids[1]}],
)
assert resp.status_code == 204
```

After bulk delete, only the non-deleted objects remain:

```python
assert client.get("/api/ipam/vlans/").json()["count"] == 1
```

## Single vs bulk detection

The same endpoint handles both individual objects and arrays. You do not need a separate URL:

| Request body | Behavior | Response |
|---|---|---|
| `{"name": "x", "vid": 1}` | Single create | Single object, 201 |
| `[{"name": "x", "vid": 1}, ...]` | Bulk create | Array of objects, 201 |
| `{"id": 1, "name": "y"}` | Single PUT/PATCH | Single object, 200 |
| `[{"id": 1, "name": "y"}, ...]` | Bulk PUT/PATCH | Array of objects, 200 |
| _(no body)_ | Single DELETE | Empty, 204 |
| `[{"id": 1}, {"id": 2}]` | Bulk DELETE | Empty, 204 |
