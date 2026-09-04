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
import os
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from netbox_sdk.mock import create_mock_app
from netbox_sdk.mock.routes import (
    RefResolver,
    _supports_ga_response_shapes,
    _value_validation_errors,
    register_netbox_mock_routes,
)
from netbox_sdk.schema import load_openapi_schema
from netbox_sdk.versioning import (
    DEFAULT_NETBOX_VERSION,
    SUPPORTED_NETBOX_VERSIONS,
    normalize_netbox_version,
    release_line,
)
from scripts.generate_typed_sdk import BACKGROUND_BULK_OVERLAY_VERSIONS

pytestmark = pytest.mark.suite_sdk


# ---------------------------------------------------------------------------
# Module-level app + per-test client with reset
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def mock_version():
    return normalize_netbox_version(os.environ.get("NETBOX_MOCK_VERSION", DEFAULT_NETBOX_VERSION))


@pytest.fixture(scope="module")
def mock_schema(mock_version):
    return load_openapi_schema(version=mock_version)


@pytest.fixture(scope="module")
def expected_mock_release(mock_schema):
    version = mock_schema.get("info", {}).get("version")
    if not isinstance(version, str) or not version:
        raise AssertionError("the selected mock schema has no evaluable info.version")
    return version


@pytest.fixture(scope="module")
def app(mock_version):
    return create_mock_app(version=mock_version)


@pytest.fixture()
def background_bulk_capability(mock_version):
    if mock_version not in BACKGROUND_BULK_OVERLAY_VERSIONS:
        pytest.skip(f"background bulk is absent from the {mock_version} release line")


@pytest.fixture()
def ga_response_shape_capability(mock_schema, mock_version):
    if not release_line(mock_version).ga_response_shapes:
        pytest.skip(f"the GA response-shape cohort is absent from the {mock_version} release line")


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


def test_netbox_status(client, expected_mock_release):
    resp = client.get("/api/status/")
    assert resp.status_code == 200
    body = resp.json()
    assert "netbox-version" in body
    assert body["netbox-version"] == expected_mock_release


def test_mock_tracks_the_selected_sdk_release_line(client, expected_mock_release):
    assert client.get("/mock/state").json()["schema_version"] == expected_mock_release


def test_ga_response_shape_detector_matches_registered_release_capabilities():
    assert DEFAULT_NETBOX_VERSION == "4.7"
    assert release_line(DEFAULT_NETBOX_VERSION).ga_response_shapes
    assert _supports_ga_response_shapes(load_openapi_schema(version=DEFAULT_NETBOX_VERSION))

    for version in SUPPORTED_NETBOX_VERSIONS:
        assert (
            _supports_ga_response_shapes(load_openapi_schema(version=version))
            is release_line(version).ga_response_shapes
        )


def test_custom_openapi_document_without_service_schema_registers():
    custom_document = {
        "openapi": "3.0.3",
        "info": {"title": "Narrow custom API", "version": "1.0.0"},
        "paths": {},
        "components": {"schemas": {}},
    }
    custom_app = FastAPI()

    state = register_netbox_mock_routes(custom_app, openapi_document=custom_document)

    assert state == {
        "route_count": 0,
        "path_count": 0,
        "method_count": 0,
        "schema_version": "1.0.0",
    }


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


def test_mock_apps_have_independent_state_namespaces():
    first = _AsgiTestClient(create_mock_app())
    second = _AsgiTestClient(create_mock_app())

    created = first.post("/api/dcim/sites/", json={"name": "First", "slug": "first"})

    assert created.status_code == 201
    assert first.get("/api/dcim/sites/").json()["count"] == 1
    assert second.get("/api/dcim/sites/").json()["count"] == 0


def test_mock_apps_isolate_branching_jobs_reset_and_route_metadata():
    first_line, second_line = SUPPORTED_NETBOX_VERSIONS[:2]
    first = _AsgiTestClient(create_mock_app(version=first_line))
    second = _AsgiTestClient(create_mock_app(version=second_line))

    first_branch = first.post(
        "/api/plugins/branching/branches/",
        json={"name": "First branch"},
    ).json()
    assert first.get("/api/plugins/branching/branches/").json()["count"] == 1
    assert second.get("/api/plugins/branching/branches/").json()["count"] == 0
    assert second.get(f"/api/plugins/branching/branches/{first_branch['id']}/").status_code == 404

    first_job = first.post(f"/api/plugins/branching/branches/{first_branch['id']}/sync/").json()
    assert second.get(f"/api/core/jobs/{first_job['id']}/").status_code == 404

    second_branch = second.post(
        "/api/plugins/branching/branches/",
        json={"name": "Second branch"},
    ).json()
    second_job = second.post(f"/api/plugins/branching/branches/{second_branch['id']}/merge/").json()
    assert first_job["id"] == second_job["id"] == 1
    assert first.get(f"/api/core/jobs/{first_job['id']}/").json()["name"] == "sync"
    assert second.get(f"/api/core/jobs/{second_job['id']}/").json()["name"] == "merge"

    assert (
        first.get("/mock/state").json()["schema_version"]
        == load_openapi_schema(version=first_line)["info"]["version"]
    )
    assert (
        second.get("/mock/state").json()["schema_version"]
        == load_openapi_schema(version=second_line)["info"]["version"]
    )

    assert first.post("/mock/reset").status_code == 200
    assert first.get("/api/plugins/branching/branches/").json()["count"] == 0
    assert first.get(f"/api/core/jobs/{first_job['id']}/").status_code == 404
    assert second.get("/api/plugins/branching/branches/").json()["count"] == 1
    assert second.get(f"/api/core/jobs/{second_job['id']}/").status_code == 200


def test_mock_rejects_exclusive_numeric_boundaries():
    resolver = RefResolver({})
    schema = {
        "type": "number",
        "minimum": 0,
        "maximum": 10,
        "exclusiveMinimum": True,
        "exclusiveMaximum": True,
    }

    assert _value_validation_errors(0, schema, resolver)
    assert _value_validation_errors(10, schema, resolver)
    assert _value_validation_errors(5, schema, resolver) == []


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
        json=[{"id": ids[1], "name": "PV2-Patched", "vid": 20}],
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


def test_bulk_validation_returns_structured_per_index_errors_atomically(client):
    resp = client.post(
        "/api/ipam/vlans/",
        json=[{"name": "Valid", "vid": 10}, "not-an-object"],
    )

    assert resp.status_code == 400
    assert resp.json() == {
        "detail": "1 of 2 objects could not be created.",
        "errors": [
            {
                "index": 1,
                "errors": {"non_field_errors": ["Expected an object."]},
            }
        ],
    }
    assert client.get("/api/ipam/vlans/").json()["count"] == 0


def test_singular_validation_rejects_missing_required_fields(client):
    response = client.post("/api/ipam/vlans/", json={"status": "active"})

    assert response.status_code == 400
    assert response.json() == {
        "name": ["This field is required."],
        "vid": ["This field is required."],
    }
    assert client.get("/api/ipam/vlans/").json()["count"] == 0


def test_bulk_validation_rejects_types_choices_and_ranges_atomically(client):
    response = client.post(
        "/api/ipam/vlans/",
        json=[
            {"name": "Valid", "vid": 10, "status": "active"},
            {"name": 42, "vid": 5000, "status": "invented"},
        ],
    )

    assert response.status_code == 400
    assert response.json()["errors"] == [
        {
            "index": 1,
            "errors": {
                "name": ["Expected string."],
                "vid": ["Ensure this value is less than or equal to 4094."],
                "status": ["'invented' is not a valid choice."],
            },
        }
    ]
    assert client.get("/api/ipam/vlans/").json()["count"] == 0


def test_unique_field_validation_is_singular_and_bulk_atomic(client):
    first = client.post("/api/dcim/sites/", json={"name": "First", "slug": "unique"})
    assert first.status_code == 201

    duplicate = client.post("/api/dcim/sites/", json={"name": "Second", "slug": "unique"})
    assert duplicate.status_code == 400
    assert duplicate.json()["slug"] == ["An object with this value already exists."]

    bulk = client.post(
        "/api/dcim/sites/",
        json=[
            {"name": "Third", "slug": "batch-duplicate"},
            {"name": "Fourth", "slug": "batch-duplicate"},
        ],
    )
    assert bulk.status_code == 400
    assert bulk.json()["errors"][0]["index"] == 1
    assert client.get("/api/dcim/sites/").json()["count"] == 1


@pytest.mark.parametrize(
    ("method", "expected_count"),
    [("POST", 1), ("PUT", 1), ("PATCH", 1), ("DELETE", 0)],
)
def test_background_bulk_is_pollable_and_eventually_mutates(
    client,
    background_bulk_capability,
    method,
    expected_count,
):
    resp = client.request(
        method,
        "/api/dcim/sites/?background=true",
        json=[{"id": 1, "name": "Queued", "slug": "queued"}],
    )

    assert resp.status_code == 202
    assert resp.json()["job"]["status"] == "pending"
    job_id = resp.json()["job"]["id"]
    assert isinstance(job_id, int)
    assert client.get("/api/dcim/sites/").json()["count"] == 0

    pending = client.get(f"/api/core/jobs/{job_id}/")
    assert pending.status_code == 200
    assert pending.json()["status"] == "pending"
    assert client.get("/api/dcim/sites/").json()["count"] == 0

    completed = client.get(f"/api/core/jobs/{job_id}/")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert client.get("/api/dcim/sites/").json()["count"] == expected_count


def test_background_bulk_failure_is_observable_and_atomic(client, background_bulk_capability):
    response = client.post(
        "/api/ipam/vlans/?background=true",
        json=[{"name": "Missing VID"}],
    )
    job_id = response.json()["job"]["id"]

    assert client.get(f"/api/core/jobs/{job_id}/").json()["status"] == "pending"
    failed = client.get(f"/api/core/jobs/{job_id}/").json()

    assert failed["status"] == "failed"
    assert "vid" in failed["error"]
    assert client.get("/api/ipam/vlans/").json()["count"] == 0


def test_ga_service_port_shapes_round_trip(client, ga_response_shape_capability):
    created = client.post(
        "/api/ipam/services/",
        json={
            "name": "https",
            "parent_object_type": "dcim.device",
            "parent_object_id": 1,
            "protocol": "tcp",
            "ports": [443],
        },
    )

    assert created.status_code == 201
    service = created.json()
    assert service["port_mappings"] == ["tcp/443"]
    assert service["protocol"] == {"value": "tcp", "label": "TCP"}
    assert service["ports"] == [443]

    updated = client.patch(
        f"/api/ipam/services/{service['id']}/",
        json={"port_mappings": ["tcp/53", "udp/53"]},
    )
    assert updated.status_code == 200
    assert updated.json()["port_mappings"] == ["tcp/53", "udp/53"]
    assert updated.json()["protocol"] is None
    assert updated.json()["ports"] is None


def _service_payload(**overrides):
    payload = {
        "name": "dns",
        "parent_object_type": "dcim.device",
        "parent_object_id": 1,
        "port_mappings": ["tcp/53"],
        "protocol": "tcp",
        "ports": [53],
    }
    payload.update(overrides)
    return payload


def test_ga_service_accepts_matching_dual_representations(client, ga_response_shape_capability):
    response = client.post("/api/ipam/services/", json=_service_payload())

    assert response.status_code == 201
    assert response.json()["port_mappings"] == ["tcp/53"]


def test_ga_service_rejects_conflicting_create(client, ga_response_shape_capability):
    response = client.post(
        "/api/ipam/services/",
        json=_service_payload(ports=[443]),
    )

    assert response.status_code == 400
    assert "ambiguous" in response.json()["non_field_errors"][0]
    assert client.get("/api/ipam/services/").json()["count"] == 0


def test_ga_service_rejects_conflicting_patch_without_mutation(
    client, ga_response_shape_capability
):
    service = client.post("/api/ipam/services/", json=_service_payload()).json()

    response = client.patch(
        f"/api/ipam/services/{service['id']}/",
        json={"port_mappings": ["udp/53"], "protocol": "tcp", "ports": [53]},
    )

    assert response.status_code == 400
    assert "ambiguous" in response.json()["non_field_errors"][0]
    stored = client.get(f"/api/ipam/services/{service['id']}/").json()
    assert stored["port_mappings"] == ["tcp/53"]


def test_ga_service_rejects_conflicting_bulk_atomically(client, ga_response_shape_capability):
    response = client.post(
        "/api/ipam/services/",
        json=[_service_payload(name="valid"), _service_payload(name="invalid", ports=[443])],
    )

    assert response.status_code == 400
    assert response.json()["errors"][0]["index"] == 1
    assert "ambiguous" in response.json()["errors"][0]["errors"]["non_field_errors"][0]
    assert client.get("/api/ipam/services/").json()["count"] == 0


def test_ga_selection_custom_fields_serialize_as_choice_objects(
    client, ga_response_shape_capability
):
    choice_set = client.post(
        "/api/extras/custom-field-choice-sets/",
        json={
            "name": "Site roles",
            "extra_choices": [["datacenter", "Data Center"], ["edge", "Edge"]],
        },
    ).json()
    for name, field_type in (("site_role", "select"), ("regions", "multiselect")):
        response = client.post(
            "/api/extras/custom-fields/",
            json={
                "name": name,
                "object_types": ["dcim.site"],
                "type": field_type,
                "choice_set": choice_set["id"],
            },
        )
        assert response.status_code == 201
    client.post(
        "/api/extras/custom-fields/",
        json={"name": "metadata", "object_types": ["dcim.site"], "type": "json"},
    )

    site = client.post(
        "/api/dcim/sites/",
        json={
            "name": "Choice Site",
            "slug": "choice-site",
            "custom_fields": {
                "site_role": "datacenter",
                "regions": ["datacenter", "edge"],
                "metadata": {"value": "raw", "label": "JSON"},
            },
        },
    ).json()

    assert site["custom_fields"] == {
        "site_role": {"value": "datacenter", "label": "Data Center"},
        "regions": [
            {"value": "datacenter", "label": "Data Center"},
            {"value": "edge", "label": "Edge"},
        ],
        "metadata": {"value": "raw", "label": "JSON"},
    }


def test_ga_selection_custom_fields_preserve_null_empty_and_unknown_values(
    client, ga_response_shape_capability
):
    choice_set = client.post(
        "/api/extras/custom-field-choice-sets/",
        json={"name": "Sparse choices", "extra_choices": [["known", "Known"]]},
    ).json()
    for name, field_type in (("nullable_role", "select"), ("sparse_regions", "multiselect")):
        response = client.post(
            "/api/extras/custom-fields/",
            json={
                "name": name,
                "object_types": ["dcim.site"],
                "type": field_type,
                "choice_set": choice_set["id"],
            },
        )
        assert response.status_code == 201

    null_and_empty = client.post(
        "/api/dcim/sites/",
        json={
            "name": "Sparse Site",
            "slug": "sparse-site",
            "custom_fields": {"nullable_role": None, "sparse_regions": []},
        },
    ).json()
    unknown = client.post(
        "/api/dcim/sites/",
        json={
            "name": "Unknown Site",
            "slug": "unknown-site",
            "custom_fields": {"nullable_role": "unknown", "sparse_regions": ["unknown"]},
        },
    ).json()

    assert null_and_empty["custom_fields"] == {"nullable_role": None, "sparse_regions": []}
    assert unknown["custom_fields"] == {
        "nullable_role": {"value": "unknown", "label": "unknown"},
        "sparse_regions": [{"value": "unknown", "label": "unknown"}],
    }


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


def test_filter_list_value_expands_to_repeated_params():
    """filter() with a list value must store list[str] in RecordSet.query.

    Before the fix: filter(tag=["a", "b"]) produced query={"tag": "['a', 'b']"}.
    After the fix:  filter(tag=["a", "b"]) must produce query={"tag": ["a", "b"]}.

    aiohttp serialises a list value as repeated params (?tag=a&tag=b) whereas a
    stringified list produces a single malformed param (?tag=%5B%27a%27%2C+...%5D).
    This test verifies the SDK facade layer correctly preserves list values.
    """
    from netbox_sdk.facade import api

    # Build an Api instance; no HTTP is issued because we only inspect RecordSet.query
    # which is built synchronously inside filter() before any network call.
    nb = api("http://localhost:8080", token="testtoken")
    record_set = nb.dcim.sites.filter(tag=["a", "b"])

    # The query dict must contain a list[str], not a stringified list.
    assert record_set.query["tag"] == ["a", "b"], (
        f"Expected query['tag'] == ['a', 'b'], got: {record_set.query['tag']!r}"
    )

    # Scalar and None values must still be coerced to str / "null".
    record_set2 = nb.dcim.sites.filter(name="router-01", status=None)
    assert record_set2.query["name"] == "router-01"
    assert record_set2.query["status"] == "null"

    # Tuples must also be treated as multi-value (same as lists).
    record_set3 = nb.dcim.sites.filter(tag=("x", "y"))
    assert record_set3.query["tag"] == ["x", "y"], (
        f"Expected tuple to become ['x', 'y'], got: {record_set3.query['tag']!r}"
    )

    # Verify the old broken behaviour no longer occurs: a stringified list must
    # NOT appear as a single value.
    assert record_set.query["tag"] != str(["a", "b"]), (
        "filter() must not str()-coerce the whole list"
    )


# ---------------------------------------------------------------------------
# Other resource types (smoke tests)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, payload",
    [
        ("/api/circuits/circuits/", {"cid": "CKT-001", "provider": 1, "type": 1}),
        ("/api/ipam/prefixes/", {"prefix": "10.0.0.0/8"}),
        ("/api/ipam/ip-addresses/", {"address": "192.168.1.1/32"}),
        ("/api/ipam/vlans/", {"name": "Test VLAN", "vid": 42}),
        ("/api/dcim/racks/", {"name": "Rack-01", "site": 1}),
        (
            "/api/dcim/devices/",
            {"name": "router-01", "device_type": 1, "role": 1, "site": 1},
        ),
        ("/api/dcim/interfaces/", {"name": "Gi0/0", "device": 1, "type": "1000base-t"}),
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
