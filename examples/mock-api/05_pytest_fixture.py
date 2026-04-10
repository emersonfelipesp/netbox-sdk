#!/usr/bin/env python3
"""Example 5: Using the Mock API in pytest tests.

Shows the recommended pytest fixture pattern for testing your own
code that calls the NetBox REST API, without needing a live instance.

This file is both runnable standalone and importable as a pytest module.

Usage:
    uv run pytest examples/mock-api/05_pytest_fixture.py -v
    uv run python examples/mock-api/05_pytest_fixture.py
"""

import pytest
from fastapi.testclient import TestClient

from netbox_sdk.mock import create_mock_app
from netbox_sdk.mock.state import reset_mock_state


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_app():
    """Create the mock FastAPI app once per test module."""
    return create_mock_app()


@pytest.fixture()
def client(mock_app):
    """Return a TestClient and reset mock state before each test."""
    with TestClient(mock_app) as c:
        # Reset ensures tests are isolated from each other
        c.post("/mock/reset")
        yield c


# ---------------------------------------------------------------------------
# Example tests
# ---------------------------------------------------------------------------


def test_site_lifecycle(client):
    """Full create → read → update → delete lifecycle for a site."""
    # Create
    resp = client.post("/api/dcim/sites/", json={"name": "Test Site", "slug": "test-site"})
    assert resp.status_code == 201
    site_id = resp.json()["id"]

    # Read list
    resp = client.get("/api/dcim/sites/")
    assert resp.json()["count"] == 1

    # Read detail
    resp = client.get(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Site"

    # Update
    resp = client.patch(f"/api/dcim/sites/{site_id}/", json={"name": "Renamed Site"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Site"

    # Delete
    assert client.delete(f"/api/dcim/sites/{site_id}/").status_code == 204

    # Gone
    assert client.get(f"/api/dcim/sites/{site_id}/").status_code == 404


def test_bulk_create_and_list(client):
    """Bulk create then paginate through results."""
    resp = client.post(
        "/api/ipam/vlans/",
        json=[{"name": f"VLAN-{i}", "vid": i} for i in range(1, 6)],
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 5

    page = client.get("/api/ipam/vlans/?limit=2&offset=0").json()
    assert page["count"] == 5
    assert len(page["results"]) == 2
    assert page["next"] is not None


def test_filter_by_name(client):
    """Create several objects and filter by name."""
    client.post(
        "/api/dcim/sites/",
        json=[
            {"name": "Alpha", "slug": "alpha"},
            {"name": "Beta", "slug": "beta"},
            {"name": "Gamma", "slug": "gamma"},
        ],
    )
    resp = client.get("/api/dcim/sites/?name=Beta")
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Beta"


def test_auto_seeded_detail(client):
    """GET on a non-existent detail ID auto-seeds a deterministic response."""
    resp = client.get("/api/dcim/sites/9999/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["id"], int)


def test_mock_reset_isolation(client):
    """Verify the reset fixture provides a clean slate for each test."""
    # After reset, all lists must be empty
    resp = client.get("/api/dcim/sites/")
    assert resp.json()["count"] == 0

    resp = client.get("/api/ipam/vlans/")
    assert resp.json()["count"] == 0


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
