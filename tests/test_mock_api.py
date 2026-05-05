"""Test suite for the netbox_sdk.mock FastAPI server.

Covers:
- CRUD lifecycle on representative NetBox resources
- Bulk create / update / delete
- Pagination envelope (count / next / previous / results)
- Query parameter filtering
- Auto-seed on unrecognised detail IDs
- State isolation via /mock/reset
- Mock server utility endpoints (health, status, state)
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from netbox_sdk.mock import create_mock_app

pytestmark = pytest.mark.suite_sdk


# ---------------------------------------------------------------------------
# Module-level app + per-test client with reset
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def app():
    return create_mock_app()


class _AsgiTestClient:
    """Small sync wrapper around ASGITransport.

    Starlette's threaded TestClient can deadlock against the generated mock
    route table on Python 3.13; ASGITransport exercises the same app without
    the blocking portal thread.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", path, **kwargs)


@pytest.fixture()
def client(app):
    c = _AsgiTestClient(app)
    c.post("/mock/reset")
    return c


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_netbox_status(client):
    resp = client.get("/api/status/")
    assert resp.status_code == 200
    body = resp.json()
    assert "netbox-version" in body
    assert body["netbox-version"].startswith("4.")


def test_mock_state_endpoint(client):
    resp = client.get("/mock/state")
    assert resp.status_code == 200
    body = resp.json()
    assert "route_count" in body
    assert "store_stats" in body
    assert body["route_count"] > 1000


def test_mock_reset_endpoint(client):
    # Populate then reset
    client.post("/api/dcim/sites/", json={"name": "Temp", "slug": "temp"})
    assert client.get("/api/dcim/sites/").json()["count"] == 1

    resp = client.post("/mock/reset")
    assert resp.status_code == 200
    assert client.get("/api/dcim/sites/").json()["count"] == 0


# ---------------------------------------------------------------------------
# Paginated list structure
# ---------------------------------------------------------------------------


def test_list_returns_pagination_envelope(client):
    resp = client.get("/api/dcim/sites/")
    assert resp.status_code == 200
    body = resp.json()
    assert "count" in body
    assert "next" in body
    assert "previous" in body
    assert "results" in body
    assert isinstance(body["results"], list)


def test_list_empty_before_create(client):
    resp = client.get("/api/dcim/sites/")
    assert resp.json()["count"] == 0
    assert resp.json()["results"] == []


# ---------------------------------------------------------------------------
# CRUD: dcim/sites
# ---------------------------------------------------------------------------


def test_create_site(client):
    resp = client.post("/api/dcim/sites/", json={"name": "London HQ", "slug": "london-hq"})
    assert resp.status_code == 201
    body = resp.json()
    assert isinstance(body["id"], int)
    assert body["name"] == "London HQ"
    assert body["slug"] == "london-hq"


def test_list_after_create(client):
    client.post("/api/dcim/sites/", json={"name": "Site A", "slug": "site-a"})
    client.post("/api/dcim/sites/", json={"name": "Site B", "slug": "site-b"})
    resp = client.get("/api/dcim/sites/")
    assert resp.json()["count"] == 2


def test_get_detail_after_create(client):
    site_id = client.post(
        "/api/dcim/sites/", json={"name": "Detail Site", "slug": "detail-site"}
    ).json()["id"]
    resp = client.get(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 200
    assert resp.json()["id"] == site_id
    assert resp.json()["name"] == "Detail Site"


def test_patch_site(client):
    site_id = client.post("/api/dcim/sites/", json={"name": "Before", "slug": "before"}).json()[
        "id"
    ]
    resp = client.patch(f"/api/dcim/sites/{site_id}/", json={"name": "After"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "After"
    assert resp.json()["id"] == site_id


def test_put_site(client):
    site_id = client.post("/api/dcim/sites/", json={"name": "Old Name", "slug": "old-name"}).json()[
        "id"
    ]
    resp = client.put(
        f"/api/dcim/sites/{site_id}/",
        json={"name": "New Name", "slug": "new-name"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_delete_site(client):
    site_id = client.post(
        "/api/dcim/sites/", json={"name": "To Delete", "slug": "to-delete"}
    ).json()["id"]
    resp = client.delete(f"/api/dcim/sites/{site_id}/")
    assert resp.status_code == 204


def test_get_deleted_site_returns_404(client):
    site_id = client.post("/api/dcim/sites/", json={"name": "Gone", "slug": "gone"}).json()["id"]
    client.delete(f"/api/dcim/sites/{site_id}/")
    assert client.get(f"/api/dcim/sites/{site_id}/").status_code == 404


def test_detail_not_in_list_after_delete(client):
    site_id = client.post("/api/dcim/sites/", json={"name": "Goodbye", "slug": "goodbye"}).json()[
        "id"
    ]
    client.delete(f"/api/dcim/sites/{site_id}/")
    ids_in_list = [s["id"] for s in client.get("/api/dcim/sites/").json()["results"]]
    assert site_id not in ids_in_list


# ---------------------------------------------------------------------------
# Auto-seed on unknown ID
# ---------------------------------------------------------------------------


def test_get_unknown_detail_auto_seeds(client):
    resp = client.get("/api/dcim/sites/9999/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["id"], int)


def test_auto_seeded_detail_is_stable(client):
    # Two GETs to the same unknown ID must return the same data
    a = client.get("/api/dcim/sites/42/").json()
    b = client.get("/api/dcim/sites/42/").json()
    assert a["id"] == b["id"]


# ---------------------------------------------------------------------------
# Bulk operations
# ---------------------------------------------------------------------------


def test_bulk_create(client):
    resp = client.post(
        "/api/ipam/vlans/",
        json=[{"name": f"VLAN-{i}", "vid": i} for i in range(1, 6)],
    )
    assert resp.status_code == 201
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 5
    assert client.get("/api/ipam/vlans/").json()["count"] == 5


def test_bulk_update_put(client):
    vlans = client.post(
        "/api/ipam/vlans/",
        json=[{"name": "V1", "vid": 1}, {"name": "V2", "vid": 2}],
    ).json()
    ids = [v["id"] for v in vlans]

    resp = client.put(
        "/api/ipam/vlans/",
        json=[{"id": ids[0], "name": "V1-Updated", "vid": 1}],
    )
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "V1-Updated"


def test_bulk_update_patch(client):
    vlans = client.post(
        "/api/ipam/vlans/",
        json=[{"name": "PV1", "vid": 10}, {"name": "PV2", "vid": 20}],
    ).json()
    ids = [v["id"] for v in vlans]

    resp = client.patch(
        "/api/ipam/vlans/",
        json=[{"id": ids[1], "name": "PV2-Patched"}],
    )
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "PV2-Patched"


def test_bulk_delete(client):
    vlans = client.post(
        "/api/ipam/vlans/",
        json=[{"name": "D1", "vid": 100}, {"name": "D2", "vid": 200}, {"name": "D3", "vid": 300}],
    ).json()
    ids = [v["id"] for v in vlans]

    resp = client.request("DELETE", "/api/ipam/vlans/", json=[{"id": ids[0]}, {"id": ids[1]}])
    assert resp.status_code == 204
    assert client.get("/api/ipam/vlans/").json()["count"] == 1


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


def test_pagination_limit_offset(client):
    client.post(
        "/api/dcim/sites/",
        json=[{"name": f"S{i}", "slug": f"s{i}"} for i in range(7)],
    )
    resp = client.get("/api/dcim/sites/?limit=3&offset=0")
    data = resp.json()
    assert data["count"] == 7
    assert len(data["results"]) == 3
    assert data["next"] is not None
    assert data["previous"] is None


def test_pagination_last_page(client):
    client.post(
        "/api/dcim/sites/",
        json=[{"name": f"P{i}", "slug": f"p{i}"} for i in range(5)],
    )
    resp = client.get("/api/dcim/sites/?limit=3&offset=3")
    data = resp.json()
    assert len(data["results"]) == 2
    assert data["next"] is None
    assert data["previous"] is not None


@pytest.fixture(scope="module")
def app_v46():
    """A NetBox 4.6 mock app — required for cursor-based pagination tests."""
    from netbox_sdk.mock import create_mock_app

    return create_mock_app(version="4.6")


@pytest.fixture()
def client_v46(app_v46):
    """Per-test client backed by the 4.6 mock app, with state reset."""
    test_client = _AsgiTestClient(app_v46)
    test_client.post("/mock/reset")
    return test_client


def test_pagination_cursor_start_param(client_v46):
    """NetBox 4.6+ cursor-based pagination via ?start=<pk>&limit=N."""
    created = client_v46.post(
        "/api/dcim/sites/",
        json=[{"name": f"C{i}", "slug": f"c{i}"} for i in range(5)],
    ).json()
    pks = sorted(item["id"] for item in created)

    resp = client_v46.get(f"/api/dcim/sites/?start={pks[0]}&limit=2")
    data = resp.json()

    assert data["count"] is None
    assert data["previous"] is None
    assert [item["id"] for item in data["results"]] == pks[:2]
    assert data["next"] is not None
    assert f"start={pks[1] + 1}" in data["next"]


def test_pagination_cursor_last_page_has_no_next(client_v46):
    created = client_v46.post(
        "/api/dcim/sites/",
        json=[{"name": f"D{i}", "slug": f"d{i}"} for i in range(3)],
    ).json()
    pks = sorted(item["id"] for item in created)

    resp = client_v46.get(f"/api/dcim/sites/?start={pks[-1]}&limit=10")
    data = resp.json()

    assert data["count"] is None
    assert data["next"] is None
    assert [item["id"] for item in data["results"]] == [pks[-1]]


def test_pagination_cursor_rejects_offset(client_v46):
    client_v46.post("/api/dcim/sites/", json={"name": "X", "slug": "x"})
    resp = client_v46.get("/api/dcim/sites/?start=1&offset=0&limit=5")
    assert resp.status_code == 400


def test_pagination_cursor_rejects_ordering(client_v46):
    client_v46.post("/api/dcim/sites/", json={"name": "X", "slug": "x"})
    resp = client_v46.get("/api/dcim/sites/?start=1&ordering=name&limit=5")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Query filtering
# ---------------------------------------------------------------------------


def test_filter_by_name(client):
    client.post(
        "/api/dcim/sites/",
        json=[
            {"name": "Alpha", "slug": "alpha"},
            {"name": "Beta", "slug": "beta"},
        ],
    )
    resp = client.get("/api/dcim/sites/?name=Alpha")
    data = resp.json()
    assert data["count"] == 1
    assert data["results"][0]["name"] == "Alpha"


def test_filter_no_matches(client):
    client.post("/api/dcim/sites/", json={"name": "Gamma", "slug": "gamma"})
    resp = client.get("/api/dcim/sites/?name=DoesNotExist")
    assert resp.json()["count"] == 0


# ---------------------------------------------------------------------------
# Other resource types (smoke tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/api/circuits/circuits/", {"cid": "CKT-001"}),
        ("/api/ipam/prefixes/", {"prefix": "10.0.0.0/8"}),
        ("/api/ipam/ip-addresses/", {"address": "192.168.1.1/32"}),
        ("/api/ipam/vlans/", {"name": "Test VLAN", "vid": 42}),
        ("/api/dcim/racks/", {"name": "Rack-01"}),
        ("/api/dcim/devices/", {"name": "router-01"}),
        ("/api/dcim/interfaces/", {"name": "Gi0/0"}),
        ("/api/tenancy/tenants/", {"name": "ACME", "slug": "acme"}),
        ("/api/virtualization/virtual-machines/", {"name": "vm-01"}),
    ],
)
def test_create_resource_smoke(client, path, payload):
    resp = client.post(path, json=payload)
    assert resp.status_code == 201, f"POST {path} returned {resp.status_code}: {resp.text}"
    body = resp.json()
    assert isinstance(body["id"], int)

    # Verify it appears in the list
    list_resp = client.get(path)
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] >= 1


# ---------------------------------------------------------------------------
# Auto-increment IDs are unique
# ---------------------------------------------------------------------------


def test_sequential_ids(client):
    ids = []
    for i in range(5):
        resp = client.post("/api/dcim/sites/", json={"name": f"Seq-{i}", "slug": f"seq-{i}"})
        ids.append(resp.json()["id"])
    assert len(set(ids)) == 5, f"Expected unique IDs, got: {ids}"
    assert ids == sorted(ids), f"Expected ascending IDs, got: {ids}"
