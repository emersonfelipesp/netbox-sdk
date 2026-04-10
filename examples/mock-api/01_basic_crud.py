#!/usr/bin/env python3
"""Example 1: Basic CRUD with the NetBox Mock API server.

Starts the mock FastAPI app in-process and exercises full
Create / Read / Update / Delete against the in-memory store.

No running NetBox instance is required.

Usage:
    uv run python examples/mock-api/01_basic_crud.py
"""

from fastapi.testclient import TestClient

from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)


def main() -> None:
    print("=" * 60)
    print("Example 1: Basic CRUD — NetBox Mock API")
    print("=" * 60)

    # --- CREATE ---
    print("\n[CREATE] POST /api/dcim/sites/")
    resp = client.post(
        "/api/dcim/sites/",
        json={"name": "New York DC", "slug": "new-york-dc"},
    )
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    site = resp.json()
    site_id = site["id"]
    print(f"    Created: id={site_id}, name={site['name']}, slug={site['slug']}")

    # --- READ (list) ---
    print("\n[READ] GET /api/dcim/sites/")
    resp = client.get("/api/dcim/sites/")
    assert resp.status_code == 200
    data = resp.json()
    print(f"    count={data['count']}, results={len(data['results'])}")

    # --- READ (detail) ---
    print(f"\n[READ] GET /api/dcim/sites/{site_id}/")
    resp = client.get(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 200
    detail = resp.json()
    print(f"    id={detail['id']}, name={detail['name']}")

    # --- UPDATE (partial) ---
    print(f"\n[PATCH] /api/dcim/sites/{site_id}/")
    resp = client.patch(f"/api/dcim/sites/{site_id}/", json={"name": "NYC Data Center"})
    assert resp.status_code == 200
    updated = resp.json()
    print(f"    Updated name: {updated['name']}")

    # --- UPDATE (full replace) ---
    print(f"\n[PUT] /api/dcim/sites/{site_id}/")
    resp = client.put(
        f"/api/dcim/sites/{site_id}/",
        json={"name": "NYC DC Final", "slug": "nyc-dc-final"},
    )
    assert resp.status_code == 200
    print(f"    Replaced name: {resp.json()['name']}")

    # --- DELETE ---
    print(f"\n[DELETE] /api/dcim/sites/{site_id}/")
    resp = client.delete(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 204
    print("    Deleted (204 No Content)")

    # --- VERIFY 404 ---
    print(f"\n[VERIFY] GET /api/dcim/sites/{site_id}/ after delete")
    resp = client.get(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 404
    print("    404 Not Found — correct!")

    print("\n" + "=" * 60)
    print("All assertions passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
