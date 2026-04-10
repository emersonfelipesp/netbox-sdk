#!/usr/bin/env python3
"""Example 3: Pagination and Filtering with the NetBox Mock API.

NetBox list endpoints support limit/offset pagination and arbitrary
query-parameter filtering. This example creates a batch of objects
then demonstrates paging and filtering through them.

Usage:
    uv run python examples/mock-api/03_pagination_filtering.py
"""

from fastapi.testclient import TestClient

from netbox_sdk.mock import create_mock_app

app = create_mock_app()
client = TestClient(app)


def main() -> None:
    print("=" * 60)
    print("Example 3: Pagination and Filtering — NetBox Mock API")
    print("=" * 60)

    # Seed 10 sites
    print("\n[SEED] Creating 10 sites...")
    sites = client.post(
        "/api/dcim/sites/",
        json=[{"name": f"Site-{i:02d}", "slug": f"site-{i:02d}"} for i in range(10)],
    ).json()
    print(f"    Created: {[s['name'] for s in sites]}")

    # --- DEFAULT PAGINATION ---
    print("\n[PAGINATION] GET /api/dcim/sites/ (default limit=50)")
    resp = client.get("/api/dcim/sites/")
    data = resp.json()
    print(f"    count={data['count']}, results returned={len(data['results'])}")
    print(f"    next={data['next']}, previous={data['previous']}")

    # --- PAGED ACCESS ---
    print("\n[PAGINATION] GET /api/dcim/sites/?limit=3&offset=0")
    resp = client.get("/api/dcim/sites/?limit=3&offset=0")
    data = resp.json()
    print(f"    Page 1: {[s['name'] for s in data['results']]}")
    print(f"    next={data['next']}")

    print("\n[PAGINATION] GET /api/dcim/sites/?limit=3&offset=3")
    resp = client.get("/api/dcim/sites/?limit=3&offset=3")
    data = resp.json()
    print(f"    Page 2: {[s['name'] for s in data['results']]}")

    # --- FILTERING ---
    print("\n[FILTER] GET /api/dcim/sites/?name=Site-05")
    resp = client.get("/api/dcim/sites/?name=Site-05")
    data = resp.json()
    print(f"    Filtered count={data['count']}, names={[s['name'] for s in data['results']]}")
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Site-05"

    # --- STATUS FILTER ---
    # Create one with a known status
    client.post("/api/dcim/sites/", json={"name": "Retired-Site", "slug": "retired-site"})
    client.patch(
        f"/api/dcim/sites/{sites[-1]['id']}/",
        json={"status": "retired"},
    )
    resp = client.get("/api/dcim/sites/?status=retired")
    data = resp.json()
    print(f"\n[FILTER] GET /api/dcim/sites/?status=retired => count={data['count']}")

    print("\n" + "=" * 60)
    print("All assertions passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
