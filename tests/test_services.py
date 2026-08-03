"""Tests for service-layer request resolution and dynamic CLI argument parsing."""

import json

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.schema import build_schema_index
from netbox_sdk.services import (
    ACTION_METHOD_MAP,
    list_all_pages,
    parse_header_pairs,
    parse_key_value_pairs,
    resolve_dynamic_request,
    run_dynamic_command,
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


def test_parse_key_value_pairs_preserves_repeated_keys():
    assert parse_key_value_pairs(["tag=prod", "tag=edge", "status=active"]) == {
        "tag": ["prod", "edge"],
        "status": "active",
    }


def test_parse_key_value_pairs_invalid():
    with pytest.raises(ValueError):
        parse_key_value_pairs(["invalid"])


def test_parse_header_pairs_accepts_colon_and_equals_forms():
    assert parse_header_pairs(['If-Match: "abc"', "Referer=https://netbox.example.com/a:b"]) == {
        "If-Match": '"abc"',
        "Referer": "https://netbox.example.com/a:b",
    }


@pytest.mark.parametrize("raw", ["If-Match", "=value", "X-Test=bad\nvalue"])
def test_parse_header_pairs_rejects_invalid_headers(raw):
    with pytest.raises(ValueError):
        parse_header_pairs([raw])


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
        self.calls: list[dict] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict | None = None,
        payload=None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "payload": payload,
                "headers": headers,
            }
        )
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


async def test_list_all_pages_preserves_repeated_next_query_and_headers():
    page1 = {
        "count": 3,
        "next": "http://netbox.example.com/api/dcim/devices/?tag=prod&tag=edge&limit=2&offset=2",
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

    await list_all_pages(
        client,
        _index(),
        "dcim",
        "devices",
        query_pairs=["status=active"],
        header_pairs=['If-Match: "etag"'],
    )

    assert client.calls[0]["query"] == {"status": "active"}
    assert client.calls[0]["headers"] == {"If-Match": '"etag"'}
    assert client.calls[1]["query"]["tag"] == ["prod", "edge"]
    assert client.calls[1]["headers"] == {"If-Match": '"etag"'}


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


async def test_list_all_pages_propagates_second_page_http_failure():
    # A later page that comes back as an error must not be silently folded
    # into a synthesized status=200 partial response — that would hide an
    # outage or permission failure from callers requesting all=true.
    page1 = {
        "count": 3,
        "next": "http://netbox.example.com/api/dcim/devices/?limit=2&offset=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    client = _MockClient(
        [
            ApiResponse(status=200, text=json.dumps(page1)),
            ApiResponse(status=500, text='{"detail": "Internal Server Error"}'),
        ]
    )
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    assert result.status == 500
    assert json.loads(result.text) == {"detail": "Internal Server Error"}


async def test_list_all_pages_propagates_second_page_non_json_failure():
    # A non-JSON error body (e.g. an HTML error page from a proxy) on a later
    # page must also propagate as a failure, not a partial 200.
    page1 = {
        "count": 3,
        "next": "http://netbox.example.com/api/dcim/devices/?limit=2&offset=2",
        "previous": None,
        "results": [{"id": 1}, {"id": 2}],
    }
    client = _MockClient(
        [
            ApiResponse(status=200, text=json.dumps(page1)),
            ApiResponse(status=502, text="<html>Bad Gateway</html>"),
        ]
    )
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    assert result.status == 502
    assert result.text == "<html>Bad Gateway</html>"


async def test_list_all_pages_first_page_error_status_not_treated_as_success():
    # Even if an error body happens to parse as JSON with a "results" key,
    # a non-2xx status on the very first page must propagate unchanged.
    raw = json.dumps({"results": [], "detail": "forbidden"})
    client = _MockClient([ApiResponse(status=403, text=raw)])
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    assert result.status == 403
    assert result.text == raw


async def test_list_all_pages_non_paginated_response():
    # If response is not a NetBox paginated envelope, return it as-is.
    raw = json.dumps([{"id": 1}])
    client = _MockClient([ApiResponse(status=200, text=raw)])
    result = await list_all_pages(client, _index(), "dcim", "devices", query_pairs=[])
    assert result.text == raw


async def test_run_dynamic_command_forwards_headers_and_repeated_query_params():
    client = _MockClient([ApiResponse(status=200, text='{"count": 0, "results": []}')])

    await run_dynamic_command(
        client,
        _index(),
        "dcim",
        "devices",
        "list",
        object_id=None,
        query_pairs=["tag=prod", "tag=edge"],
        header_pairs=['If-Match: "etag"'],
        body_json=None,
        body_file=None,
    )

    assert client.calls[0]["query"] == {"tag": ["prod", "edge"]}
    assert client.calls[0]["headers"] == {"If-Match": '"etag"'}
