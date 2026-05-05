from __future__ import annotations

import io

import pytest

from netbox_sdk import (
    AllocationError,
    ApiResponse,
    Config,
    ContentError,
    NetBoxApiClient,
    ParameterValidationError,
    RequestError,
    api,
    async_api,
    build_schema_index,
)
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk


class _FakeClient:
    def __init__(self, responses: dict[tuple[str, str], list[ApiResponse] | ApiResponse]):
        self.responses = responses
        self.calls: list[dict] = []
        self._default_headers: dict[str, str] = {}

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        payload=None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> ApiResponse:
        merged_headers = dict(self._default_headers)
        merged_headers.update(headers or {})
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "payload": payload,
                "headers": merged_headers,
                "expect_json": expect_json,
            }
        )
        key = (method.upper(), path)
        value = self.responses[key]
        if isinstance(value, list):
            return value.pop(0)
        return value

    async def status(self):
        return {"netbox-version": "4.2"}

    async def openapi(self):
        return {"openapi": "3.0.0", "paths": {}}

    async def get_version(self):
        return "4.2"

    async def create_token(self, username: str, password: str):
        return ApiResponse(
            status=201,
            text='{"id": 7, "key": "abc123", "username": "admin"}',
            headers={},
        )

    from contextlib import contextmanager

    @contextmanager
    def header_scope(self, **headers: str):
        previous = dict(self._default_headers)
        self._default_headers.update(headers)
        try:
            yield self
        finally:
            self._default_headers = previous


@pytest.mark.asyncio
async def test_async_api_enriches_runtime_plugin_resources() -> None:
    class _RuntimeFakeClient(_FakeClient):
        async def request(
            self,
            method: str,
            path: str,
            *,
            query: dict[str, str] | None = None,
            payload=None,
            headers: dict[str, str] | None = None,
            expect_json: bool = True,
        ) -> ApiResponse:
            if method == "GET" and path == "/api/plugins/":
                return ApiResponse(status=200, text="{}", headers={})
            if method == "GET" and path == "/api/core/object-types/":
                return ApiResponse(
                    status=200,
                    text=(
                        '{"count": 1, "next": null, "results": ['
                        '{"public": true, "rest_api_endpoint": "/api/plugins/custom/widgets/"}'
                        "]}"
                    ),
                    headers={},
                )
            if method == "OPTIONS" and path == "/api/plugins/custom/widgets/":
                return ApiResponse(
                    status=200,
                    text='{"actions": {"POST": {}}}',
                    headers={"Allow": "GET, POST, OPTIONS"},
                )
            return await super().request(
                method,
                path,
                query=query,
                payload=payload,
                headers=headers,
                expect_json=expect_json,
            )

    nb = await async_api(
        "https://netbox.example.com",
        token="tok",
        client=_RuntimeFakeClient({}),
    )

    paths = nb.schema.resource_paths("plugins", "custom/widgets")
    assert paths is not None
    assert paths.list_path == "/api/plugins/custom/widgets/"


@pytest.mark.asyncio
async def test_api_filter_strict_validation_raises_for_unknown_parameter() -> None:
    nb = api(
        "https://netbox.example.com",
        token="tok",
        strict_filters=True,
        client=_FakeClient({}),
        schema=build_schema_index(OPENAPI_PATH),
    )

    with pytest.raises(ParameterValidationError):
        nb.dcim.devices.filter(not_a_real_filter="value")


@pytest.mark.asyncio
async def test_recordset_follows_paginated_next_links() -> None:
    """Offset-mode RecordSet still follows the response 'next' URL verbatim."""
    client = _FakeClient({})
    client.responses[("GET", "/api/dcim/devices/")] = [
        ApiResponse(
            status=200,
            text='{"count": 2, "next": "https://netbox.example.com/api/dcim/devices/?limit=1&offset=1", "results": [{"id": 1, "name": "leaf1", "url": "https://netbox.example.com/api/dcim/devices/1/"}]}',
            headers={},
        ),
        ApiResponse(
            status=200,
            text='{"count": 2, "next": null, "results": [{"id": 2, "name": "leaf2", "url": "https://netbox.example.com/api/dcim/devices/2/"}]}',
            headers={},
        ),
    ]
    # _FakeClient.get_version() returns "4.2", which resolves to offset mode.
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    names = []
    async for device in nb.dcim.devices.all(limit=1):
        names.append(device.name)

    assert names == ["leaf1", "leaf2"]
    assert client.calls[1]["query"] == {"limit": "1", "offset": "1"}


@pytest.mark.asyncio
async def test_recordset_uses_cursor_pagination_against_netbox_46() -> None:
    """Auto mode resolves to cursor on NetBox 4.6+ and drives next pages by start=last_pk+1."""

    class _CursorFakeClient(_FakeClient):
        async def get_version(self) -> str:  # type: ignore[override]
            return "4.6.0"

    client = _CursorFakeClient({})
    client.responses[("GET", "/api/dcim/devices/")] = [
        ApiResponse(
            status=200,
            text='{"count": null, "next": null, "results": ['
            '{"id": 1, "name": "leaf1", "url": "https://netbox.example.com/api/dcim/devices/1/"},'
            '{"id": 2, "name": "leaf2", "url": "https://netbox.example.com/api/dcim/devices/2/"}'
            "]}",
            headers={},
        ),
        ApiResponse(
            status=200,
            text='{"count": null, "next": null, "results": ['
            '{"id": 5, "name": "leaf3", "url": "https://netbox.example.com/api/dcim/devices/5/"}'
            "]}",
            headers={},
        ),
    ]
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    names = []
    async for device in nb.dcim.devices.all(limit=2):
        names.append(device.name)

    assert names == ["leaf1", "leaf2", "leaf3"]
    assert client.calls[0]["query"] == {"start": "0", "limit": "2"}
    # Second page starts after the last seen pk (2 + 1 = 3).
    assert client.calls[1]["query"] == {"start": "3", "limit": "2"}


@pytest.mark.asyncio
async def test_detail_endpoint_supports_json_and_raw_modes() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/racks/3/"): ApiResponse(
                status=200,
                text='{"id": 3, "name": "Rack-3", "url": "https://netbox.example.com/api/dcim/racks/3/"}',
                headers={},
            ),
            ("GET", "/api/dcim/racks/3/elevation/"): [
                ApiResponse(status=200, text='[{"id": 30}]', headers={}),
                ApiResponse(
                    status=200, text="<svg>rack</svg>", headers={"Content-Type": "image/svg+xml"}
                ),
            ],
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    rack = await nb.dcim.racks.get(3)
    units = await rack.elevation.list()
    svg = await rack.elevation.list(render="svg")

    assert units == [{"id": 30}]
    assert svg == "<svg>rack</svg>"
    assert client.calls[-1]["expect_json"] is False


@pytest.mark.asyncio
async def test_available_prefixes_conflict_raises_allocation_error() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/ipam/prefixes/9/"): ApiResponse(
                status=200,
                text='{"id": 9, "prefix": "10.0.0.0/24", "url": "https://netbox.example.com/api/ipam/prefixes/9/"}',
                headers={},
            ),
            ("POST", "/api/ipam/prefixes/9/available-prefixes/"): ApiResponse(
                status=409,
                text='{"detail": "No allocation available"}',
                headers={},
            ),
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    prefix = await nb.ipam.prefixes.get(9)
    with pytest.raises(AllocationError):
        await prefix.available_prefixes.create({"prefix_length": 28})


@pytest.mark.asyncio
async def test_record_supports_save_and_full_details() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/"): ApiResponse(
                status=200,
                text='{"count": 1, "next": null, "results": [{"id": 1, "name": "leaf1", "url": "https://netbox.example.com/api/dcim/devices/1/"}]}',
                headers={},
            ),
            ("GET", "/api/dcim/devices/1/"): ApiResponse(
                status=200,
                text='{"id": 1, "name": "leaf1", "serial": "ABC", "url": "https://netbox.example.com/api/dcim/devices/1/"}',
                headers={},
            ),
            ("PATCH", "/api/dcim/devices/1/"): ApiResponse(
                status=200,
                text='{"id": 1, "name": "leaf1-renamed", "serial": "ABC", "url": "https://netbox.example.com/api/dcim/devices/1/"}',
                headers={},
            ),
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    device = await nb.dcim.devices.filter(name="leaf1").to_list(limit_override=1)
    record = device[0]
    await record.full_details()
    record.name = "leaf1-renamed"
    changed = record.updates()
    result = await record.save()

    assert record.serial == "ABC"
    assert changed == {"name": "leaf1-renamed"}
    assert result is True
    assert client.calls[-1]["payload"] == {"name": "leaf1-renamed"}


@pytest.mark.asyncio
async def test_activate_branch_scopes_header_for_nested_requests() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/1/"): ApiResponse(
                status=200,
                text='{"id": 1, "name": "leaf1", "url": "https://netbox.example.com/api/dcim/devices/1/"}',
                headers={},
            )
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    class _Branch:
        schema_id = "feature-branch"

    with nb.activate_branch(_Branch()):
        await nb.dcim.devices.get(1)

    assert client.calls[0]["headers"]["X-NetBox-Branch"] == "feature-branch"


@pytest.mark.asyncio
async def test_api_exposes_status_openapi_and_token_provisioning() -> None:
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=_FakeClient({}),
        schema=build_schema_index(OPENAPI_PATH),
    )

    status = await nb.status()
    spec = await nb.openapi()
    token = await nb.create_token("admin", "password")

    assert status["netbox-version"] == "4.2"
    assert spec["openapi"] == "3.0.0"
    assert token.id == 7
    assert token.key == "abc123"


def test_client_extracts_files_into_multipart_form() -> None:
    client = NetBoxApiClient(
        Config(base_url="https://netbox.example.com", token_version="v1", token_secret="tok")
    )
    clean_payload, form = client._extract_files(
        {
            "name": "image-1",
            "image": ("photo.png", io.BytesIO(b"abc"), "image/png"),
        }
    )

    assert clean_payload == {"name": "image-1"}
    assert form is not None


@pytest.mark.asyncio
async def test_invalid_json_raises_content_error() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/plugins/installed-plugins"): ApiResponse(
                status=200,
                text="not-json",
                headers={},
            )
        }
    )
    nb = api("https://netbox.example.com", token="tok", client=client)

    with pytest.raises(ContentError):
        await nb.plugins.installed_plugins()


@pytest.mark.asyncio
async def test_get_returns_none_on_404() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/404/"): ApiResponse(
                status=404,
                text='{"detail": "Not found."}',
                headers={},
            )
        }
    )
    nb = api("https://netbox.example.com", token="tok", client=client)

    record = await nb.dcim.devices.get(404)

    assert record is None


@pytest.mark.asyncio
async def test_non_detail_errors_raise_request_error() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/1/"): ApiResponse(
                status=500,
                text='{"detail": "boom"}',
                headers={},
            )
        }
    )
    nb = api("https://netbox.example.com", token="tok", client=client)

    with pytest.raises(RequestError):
        await nb.dcim.devices.get(1)


@pytest.mark.asyncio
async def test_recordset_delete_materialises_and_dispatches_ids() -> None:
    """RecordSet.delete() must drain the iterator and DELETE the resolved ids.

    Previously RecordSet.delete() passed self into Endpoint.delete(), which
    rejects RecordSet instances and always raised ValueError, so the method
    was completely broken.
    """
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/"): [
                ApiResponse(
                    status=200,
                    text=(
                        '{"count": 2, "next": null, "results": ['
                        '{"id": 11, "name": "a", "url": "https://netbox.example.com/api/dcim/devices/11/"},'
                        '{"id": 12, "name": "b", "url": "https://netbox.example.com/api/dcim/devices/12/"}'
                        "]}"
                    ),
                    headers={},
                )
            ],
            ("DELETE", "/api/dcim/devices/"): ApiResponse(status=204, text="", headers={}),
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    rs = nb.dcim.devices.filter(role="leaf")
    result = await rs.delete()

    assert result is True
    delete_call = next(c for c in client.calls if c["method"] == "DELETE")
    assert delete_call["payload"] == [11, 12]


@pytest.mark.asyncio
async def test_recordset_delete_on_empty_set_is_noop() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/dcim/devices/"): ApiResponse(
                status=200,
                text='{"count": 0, "next": null, "results": []}',
                headers={},
            )
        }
    )
    nb = api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
    )

    result = await nb.dcim.devices.filter(role="ghost").delete()

    assert result is True
    assert not any(c["method"] == "DELETE" for c in client.calls)
