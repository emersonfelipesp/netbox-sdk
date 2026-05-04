#!/usr/bin/env python3
"""Example 2: Bulk Operations with the NetBox Mock API.

Demonstrates bulk create, bulk update, and bulk delete — NetBox
list endpoints accept arrays in POST/PUT/PATCH/DELETE request bodies.

Usage:
    uv run python examples/mock-api/02_bulk_operations.py
"""

from fastapi.testclient import TestClient

from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)


def main() -> None:
    print("=" * 60)
    print("Example 2: Bulk Operations — NetBox Mock API")
    print("=" * 60)

    # --- BULK CREATE ---
    print("\n[BULK CREATE] POST /api/ipam/vlans/ with array")
    resp = client.post(
        "/api/ipam/vlans/",
        json=[
            {"name": "Management", "vid": 1},
            {"name": "Production", "vid": 100},
            {"name": "DMZ", "vid": 200},
            {"name": "Backup", "vid": 300},
        ],
    )
    assert resp.status_code == 201
    vlans = resp.json()
    assert isinstance(vlans, list) and len(vlans) == 4
    vlan_ids = [v["id"] for v in vlans]
    print(f"    Created {len(vlans)} VLANs: {[(v['name'], v['vid']) for v in vlans]}")

    # --- VERIFY LIST ---
    resp = client.get("/api/ipam/vlans/")
    print(f"    List count: {resp.json()['count']}")

    # --- BULK UPDATE (PUT) ---
    print("\n[BULK UPDATE] PUT /api/ipam/vlans/ with updated names")
    resp = client.put(
        "/api/ipam/vlans/",
        json=[
            {"id": vlan_ids[0], "name": "MGMT", "vid": 1},
            {"id": vlan_ids[1], "name": "PROD", "vid": 100},
        ],
    )
    assert resp.status_code == 200
    updated = resp.json()
    print(f"    Updated names: {[v['name'] for v in updated]}")

    # --- BULK PATCH ---
    print("\n[BULK PATCH] PATCH /api/ipam/vlans/ — partial update")
    resp = client.patch(
        "/api/ipam/vlans/",
        json=[
            {"id": vlan_ids[2], "name": "DMZ-Updated"},
        ],
    )
    assert resp.status_code == 200
    print(f"    Patched: {resp.json()[0]['name']}")

    # --- BULK DELETE ---
    print("\n[BULK DELETE] DELETE /api/ipam/vlans/ with id list")
    resp = client.request(
        "DELETE",
        "/api/ipam/vlans/",
        json=[{"id": vlan_ids[0]}, {"id": vlan_ids[1]}],
    )
    assert resp.status_code == 204
    print("    Deleted 2 VLANs (204 No Content)")

    resp = client.get("/api/ipam/vlans/")
    print(f"    Remaining VLANs: {resp.json()['count']} (expected 2)")

    print("\n" + "=" * 60)
    print("All assertions passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
