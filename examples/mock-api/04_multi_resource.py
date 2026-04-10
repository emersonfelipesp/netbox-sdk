#!/usr/bin/env python3
"""Example 4: Multi-resource workflows with the NetBox Mock API.

Shows how to wire together multiple NetBox resource types —
e.g. create a site, then racks, then devices — all against
the in-memory mock with no real NetBox needed.

Usage:
    uv run python examples/mock-api/04_multi_resource.py
"""

from fastapi.testclient import TestClient

from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)


def post(path: str, payload: dict) -> dict:
    resp = client.post(path, json=payload)
    assert resp.status_code == 201, f"POST {path} returned {resp.status_code}: {resp.text}"
    return resp.json()


def get(path: str) -> dict:
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.json()


def main() -> None:
    print("=" * 60)
    print("Example 4: Multi-Resource Workflow — NetBox Mock API")
    print("=" * 60)

    # 1. Create a site
    print("\n[1] Create site")
    site = post("/api/dcim/sites/", {"name": "Primary DC", "slug": "primary-dc"})
    print(f"    Site: id={site['id']}, name={site['name']}")

    # 2. Create a tenant
    print("\n[2] Create tenant")
    tenant = post("/api/tenancy/tenants/", {"name": "Acme Corp", "slug": "acme-corp"})
    print(f"    Tenant: id={tenant['id']}, name={tenant['name']}")

    # 3. Create a rack at the site
    print("\n[3] Create rack")
    rack = post("/api/dcim/racks/", {"name": "Rack-A01", "site": site["id"]})
    print(f"    Rack: id={rack['id']}, name={rack['name']}")

    # 4. Create a manufacturer + device type
    print("\n[4] Create manufacturer and device type")
    mfr = post("/api/dcim/manufacturers/", {"name": "Cisco", "slug": "cisco"})
    dtype = post(
        "/api/dcim/device-types/",
        {"model": "Nexus 9300", "slug": "nexus-9300", "manufacturer": mfr["id"]},
    )
    print(f"    Manufacturer: {mfr['name']}, Device Type: {dtype['model']}")

    # 5. Create a device role
    print("\n[5] Create device role")
    role = post("/api/dcim/device-roles/", {"name": "Core Switch", "slug": "core-switch"})
    print(f"    Role: {role['name']}")

    # 6. Create a device
    print("\n[6] Create device")
    device = post(
        "/api/dcim/devices/",
        {
            "name": "sw-core-01",
            "site": site["id"],
            "rack": rack["id"],
            "device_type": dtype["id"],
            "role": role["id"],
            "tenant": tenant["id"],
        },
    )
    print(f"    Device: id={device['id']}, name={device['name']}")

    # 7. Create IP addresses
    print("\n[7] Create IP prefixes and addresses")
    prefix = post("/api/ipam/prefixes/", {"prefix": "10.0.0.0/24"})
    ip = post("/api/ipam/ip-addresses/", {"address": "10.0.0.1/24"})
    print(f"    Prefix: {prefix['prefix']}, IP: {ip['address']}")

    # 8. Verify state
    print("\n[8] Verify store state")
    resp = client.get("/mock/state")
    state = resp.json()
    print(f"    Objects in store: {state['store_stats']['objects']}")
    print(f"    Collections in store: {state['store_stats']['collections']}")

    # Summary counts
    for resource in ("sites", "racks", "devices", "manufacturers"):
        data = get(f"/api/dcim/{resource}/")
        print(f"    /api/dcim/{resource}/: count={data['count']}")

    print("\n" + "=" * 60)
    print("All assertions passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
