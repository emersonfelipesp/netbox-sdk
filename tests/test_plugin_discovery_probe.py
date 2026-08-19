"""Capability discovery must ask a routable URL, and pagination must terminate.

Discovery derived a detail template ending in ``{id}`` and sent ``OPTIONS`` to
that literal placeholder. A real DRF router requires a concrete identifier, so it
answered 404 and discovery silently fell back to GET-only — hiding the PATCH,
PUT and DELETE the endpoint actually supported.
"""

from __future__ import annotations

from typing import Any

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.plugin_discovery import (
    MAX_DISCOVERY_PAGES,
    _concrete_detail_probe,
    discover_object_type_resources,
    discover_plugin_resources,
)

pytestmark = pytest.mark.suite_sdk

_LIST = "/api/plugins/custom/widgets/"


class _Router:
    """A fake that routes like DRF: only a concrete record URL exists."""

    def __init__(self, record: dict[str, Any] | None, *, deny_options: bool = False) -> None:
        self.record = record
        self.deny_options = deny_options
        self.requests: list[tuple[str, str]] = []

    async def request(
        self, method: str, path: str, *, query: dict[str, list[str]] | None = None
    ) -> ApiResponse:
        self.requests.append((method, path))
        import json as _json

        if method == "GET" and path == "/api/plugins/":
            return ApiResponse(status=200, text=_json.dumps({"custom": f"{_LIST}"}), headers={})
        if method == "GET" and path == _LIST:
            results = [self.record] if self.record is not None else []
            return ApiResponse(
                status=200,
                text=_json.dumps({"count": len(results), "next": None, "results": results}),
                headers={},
            )
        if method == "OPTIONS" and path == _LIST:
            return ApiResponse(
                status=200,
                text='{"actions": {"POST": {}}}',
                headers={"Allow": "GET, POST, OPTIONS"},
            )
        if method == "OPTIONS" and path == f"{_LIST}17/":
            if self.deny_options:
                return ApiResponse(status=403, text="", headers={})
            return ApiResponse(
                status=200,
                text='{"actions": {"PATCH": {}, "DELETE": {}}}',
                headers={"Allow": "GET, PATCH, DELETE, OPTIONS"},
            )
        # Anything else — crucially the literal "{id}" template — does not route.
        return ApiResponse(status=404, text="", headers={})


async def test_write_methods_are_discovered_via_a_concrete_record() -> None:
    client = _Router({"id": 17, "url": f"{_LIST}17/"})

    resources = await discover_plugin_resources(client)  # type: ignore[arg-type]

    assert len(resources) == 1
    resource = resources[0]
    assert resource.detail_path == f"{_LIST}{{id}}/", "the published template stays templated"
    assert set(resource.detail_methods) >= {"GET", "PATCH", "DELETE"}
    assert ("OPTIONS", f"{_LIST}17/") in client.requests
    assert ("OPTIONS", f"{_LIST}{{id}}/") not in client.requests
    assert not any(m in {"POST", "PUT", "PATCH", "DELETE"} for m, _ in client.requests), (
        "discovery must never send a mutation"
    )


async def test_empty_collection_stays_get_only() -> None:
    """With no sample there is no safe probe, so nothing may be inferred."""
    client = _Router(None)

    resources = await discover_plugin_resources(client)  # type: ignore[arg-type]

    assert resources[0].detail_methods == ("GET",)
    assert not any(method == "OPTIONS" and "{id}" in path for method, path in client.requests)


async def test_denied_options_stays_get_only() -> None:
    """A 403 on the probe means unknown, and unknown must not become 'writable'."""
    client = _Router({"id": 17, "url": f"{_LIST}17/"}, deny_options=True)

    resources = await discover_plugin_resources(client)  # type: ignore[arg-type]

    assert resources[0].detail_methods == ("GET",)


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        pytest.param({"id": 17, "url": f"{_LIST}17/"}, f"{_LIST}17/", id="record-url"),
        pytest.param({"id": 17}, f"{_LIST}17/", id="falls-back-to-id"),
        pytest.param({"pk": 42}, f"{_LIST}42/", id="falls-back-to-pk"),
        pytest.param({"id": "a b"}, f"{_LIST}a%20b/", id="identifier-is-encoded"),
        pytest.param(
            {"id": "../../dcim/devices/1"},
            f"{_LIST}..%2F..%2Fdcim%2Fdevices%2F1/",
            id="traversal-in-id-cannot-inject-segments",
        ),
        pytest.param({}, None, id="no-identifier"),
        pytest.param(None, None, id="no-record"),
    ],
)
def test_probe_derivation(record: dict[str, Any] | None, expected: str | None) -> None:
    assert _concrete_detail_probe(_LIST, record) == expected


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("https://evil.example/api/other/things/1/", id="external-host"),
        pytest.param("/api/dcim/devices/1/", id="escapes-the-collection"),
        pytest.param(f"{_LIST}17/sub/", id="too-deep"),
        pytest.param("/not-an-api/17/", id="not-an-api-path"),
    ],
)
def test_unsafe_record_urls_are_rejected(url: str) -> None:
    """A plugin can serialize anything into ``url``; only a direct child is trusted."""
    probe = _concrete_detail_probe(_LIST, {"url": url})

    assert probe != url
    assert probe is None or probe.startswith(_LIST)


class _Paginated:
    """An object-type collection whose ``next`` chain is hostile."""

    def __init__(self, *, cyclic: bool) -> None:
        self.cyclic = cyclic
        self.queries: list[dict[str, list[str]] | None] = []
        self.pages = 0

    async def request(
        self, method: str, path: str, *, query: dict[str, list[str]] | None = None
    ) -> ApiResponse:
        import json as _json

        if method == "OPTIONS":
            return ApiResponse(status=200, text="{}", headers={"Allow": "GET, OPTIONS"})
        if path == "/api/core/object-types/":
            self.queries.append(query)
            self.pages += 1
            next_url = (
                "/api/core/object-types/?tag=a&tag=b&offset=50"
                if self.cyclic or self.pages == 1
                else None
            )
            return ApiResponse(
                status=200,
                text=_json.dumps({"count": 0, "next": next_url, "results": []}),
                headers={},
            )
        return ApiResponse(status=200, text='{"count": 0, "results": []}', headers={})


async def test_repeated_query_keys_survive_pagination() -> None:
    """``?tag=a&tag=b`` collapsed to ``tag=b``, so page two used a different filter."""
    client = _Paginated(cyclic=False)

    await discover_object_type_resources(client)  # type: ignore[arg-type]

    assert client.queries[1] == {"tag": ["a", "b"], "offset": ["50"]}


async def test_a_cyclic_next_chain_terminates() -> None:
    """A ``next`` that points back at an earlier page must not loop forever."""
    client = _Paginated(cyclic=True)

    await discover_object_type_resources(client)  # type: ignore[arg-type]

    assert client.pages <= MAX_DISCOVERY_PAGES
    assert client.pages == 2, f"stopped after {client.pages} pages, expected the repeat to end it"
