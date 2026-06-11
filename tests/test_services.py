"""Tests for service-layer request resolution and dynamic CLI argument parsing."""

import json

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.schema import build_schema_index
from netbox_sdk.services import (
    ACTION_METHOD_MAP,
    list_all_pages,
    parse_key_value_pairs,
    resolve_dynamic_request,
)
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk


def _index():
    return build_schema_index(OPENAPI_PATH)


def test_parse_key_value_pairs_ok():
    assert parse_key_value_pairs(["name=switch01", "role=leaf"]) == {
        "name": "switch01",
        "role": "leaf",
    }


def test_parse_key_value_pairs_invalid():
    with pytest.raises(ValueError):
        parse_key_value_pairs(["invalid"])


def test_resolve_list_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "list",
        object_id=None,
        query={},
        payload=None,
    )
    assert resolved.method == "GET"
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_get_requires_id():
    with pytest.raises(ValueError):
        resolve_dynamic_request(
            _index(),
            "dcim",
            "devices",
            "get",
            object_id=None,
            query={},
            payload=None,
        )


def test_resolve_get_detail_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "get",
        object_id=12,
        query={},
        payload=None,
    )
    assert resolved.method == "GET"
    assert resolved.path == "/api/dcim/devices/12/"


# --- bulk operations ---


def test_action_method_map_includes_bulk_ops():
    assert ACTION_METHOD_MAP["bulk-update"] == "PUT"
    assert ACTION_METHOD_MAP["bulk-patch"] == "PATCH"
    assert ACTION_METHOD_MAP["bulk-delete"] == "DELETE"


def test_resolve_bulk_update_uses_list_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "bulk-update",
        object_id=None,
        query={},
        payload=[{"id": 1, "name": "new"}],
    )
    assert resolved.method == "PUT"
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_bulk_patch_uses_list_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "bulk-patch",
        object_id=None,
        query={},
        payload=[{"id": 1}],
    )
    assert resolved.method == "PATCH"
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_bulk_delete_uses_list_path():
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "bulk-delete",
        object_id=None,
        query={},
        payload=[{"id": 1}],
    )
    assert resolved.method == "DELETE"
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_bulk_does_not_require_id():
    # Bulk actions must succeed even when object_id is None.
    for action in ("bulk-update", "bulk-patch", "bulk-delete"):
        resolved = resolve_dynamic_request(
            _index(),
            "dcim",
            "devices",
            action,
            object_id=None,
            query={},
            payload=[{"id": 99}],
        )
        assert resolved.path == "/api/dcim/devices/"


def test_resolve_bulk_id_is_ignored():
    # If --id is accidentally passed for a bulk action it is silently ignored
    # (bulk routes to list path regardless).
    resolved = resolve_dynamic_request(
        _index(),
        "dcim",
        "devices",
        "bulk-update",
        object_id=42,
        query={},
        payload=[{"id": 42, "name": "x"}],
    )
    assert "{id}" not in resolved.path
    assert resolved.path == "/api/dcim/devices/"


def test_resolve_detail_still_requires_id_after_bulk_support():
    # Existing detail-action contract must not be broken.
    with pytest.raises(ValueError, match="requires --id"):
        resolve_dynamic_request(
            _index(),
            "dcim",
            "devices",
            "update",
            object_id=None,
            query={},
            payload={"name": "x"},
        )


# --- list_all_pages ---


class _MockClient:
    """Minimal client stub that returns pre-configured ApiResponse objects per call index."""

    def __init__(self, responses: list[ApiResponse]) -> None:
        self._responses = responses
        self._call = 0

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict | None = None,
        payload=None,
    ) -> ApiResponse:
        resp = self._responses[self._call]
        self._call += 1
        return resp


async def test_list_all_pages_single_page():
    page = {"count": 2, "next": None, "previous": None, "results": [{"id": 1}, {"id": 2}]}
    client = _MockClient([ApiResponse(status=200, text=json.dumps(page))])
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    data = json.loads(result.text)
    assert data["count"] == 2
    assert len(data["results"]) == 2
    assert data["next"] is None


async def test_list_all_pages_multi_page():
    page1 = {
        "count": 3,
        "next": "http://netbox.example.com/api/dcim/devices/?limit=2&offset=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    page2 = {"count": 3, "next": None, "previous": None, "results": [{"id": 3}]}
    client = _MockClient(
        [
            ApiResponse(status=200, text=json.dumps(page1)),
            ApiResponse(status=200, text=json.dumps(page2)),
        ]
    )
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    data = json.loads(result.text)
    assert data["count"] == 3
    assert [r["id"] for r in data["results"]] == [1, 2, 3]


async def test_list_all_pages_respects_max_records():
    page1 = {
        "count": 4,
        "next": "http://netbox.example.com/api/dcim/devices/?limit=2&offset=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    page2 = {"count": 4, "next": None, "previous": None, "results": [{"id": 3}, {"id": 4}]}
    client = _MockClient(
        [
            ApiResponse(status=200, text=json.dumps(page1)),
            ApiResponse(status=200, text=json.dumps(page2)),
        ]
    )
    result = await list_all_pages(
        client, _index(), "dcim", "devices", query_pairs=[], max_records=3
    )
    data = json.loads(result.text)
    assert len(data["results"]) == 3


async def test_list_all_pages_non_paginated_response():
    # If response is not a NetBox paginated envelope, return it as-is.
    raw = json.dumps([{"id": 1}])
    client = _MockClient([ApiResponse(status=200, text=raw)])
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    assert result.text == raw
