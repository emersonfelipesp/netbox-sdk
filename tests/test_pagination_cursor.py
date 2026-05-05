"""Cursor-based pagination tests for the netbox_sdk facade (issue #18)."""

from __future__ import annotations

import pytest

from netbox_sdk import ApiResponse, api, build_schema_index
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk


class _RecordingClient:
    """Minimal async client stub that records calls and replays scripted responses."""

    def __init__(
        self,
        responses: dict[tuple[str, str], list[ApiResponse]] | None = None,
        *,
        version: str = "4.6.0",
    ) -> None:
        self.responses: dict[tuple[str, str], list[ApiResponse]] = responses or {}
        self.calls: list[dict] = []
        self._version = version
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
        self.calls.append({"method": method, "path": path, "query": query})
        key = (method.upper(), path)
        responses = self.responses[key]
        return responses.pop(0)

    async def status(self):
        return {"netbox-version": self._version}

    async def get_version(self):
        return self._version


def _build_api(client: _RecordingClient, **kwargs):
    return api(
        "https://netbox.example.com",
        token="tok",
        client=client,
        schema=build_schema_index(OPENAPI_PATH),
        **kwargs,
    )


def _devices_response(items: list[dict]) -> ApiResponse:
    import json

    return ApiResponse(
        status=200,
        text=json.dumps({"count": None, "next": None, "previous": None, "results": items}),
        headers={},
    )


def _device(pk: int) -> dict:
    return {
        "id": pk,
        "name": f"device-{pk}",
        "url": f"https://netbox.example.com/api/dcim/devices/{pk}/",
    }


@pytest.mark.asyncio
async def test_cursor_stops_on_short_page() -> None:
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                _devices_response([_device(1), _device(2)]),
                _devices_response([_device(7)]),  # short page → stop
            ]
        }
    )
    nb = _build_api(client)

    pks = [d.id async for d in nb.dcim.devices.all(limit=2)]

    assert pks == [1, 2, 7]
    assert len(client.calls) == 2
    assert client.calls[0]["query"] == {"start": "0", "limit": "2"}
    assert client.calls[1]["query"] == {"start": "3", "limit": "2"}


@pytest.mark.asyncio
async def test_cursor_stops_on_empty_page() -> None:
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                _devices_response([_device(1), _device(2)]),
                _devices_response([_device(3), _device(4)]),
                _devices_response([]),  # empty → stop
            ]
        }
    )
    nb = _build_api(client)

    pks = [d.id async for d in nb.dcim.devices.all(limit=2)]

    assert pks == [1, 2, 3, 4]
    assert len(client.calls) == 3


@pytest.mark.asyncio
async def test_cursor_default_uses_default_page_size_when_limit_zero() -> None:
    client = _RecordingClient(
        {("GET", "/api/dcim/devices/"): [_devices_response([_device(i) for i in range(1, 4)])]}
    )
    nb = _build_api(client)

    pks = [d.id async for d in nb.dcim.devices.all()]

    assert pks == [1, 2, 3]
    assert client.calls[0]["query"] == {"start": "0", "limit": "50"}


@pytest.mark.asyncio
async def test_auto_mode_resolves_to_offset_for_old_netbox() -> None:
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                ApiResponse(
                    status=200,
                    text='{"count": 1, "next": null, "previous": null, "results": [{"id": 9, "name": "leaf", "url": "https://netbox.example.com/api/dcim/devices/9/"}]}',
                    headers={},
                )
            ]
        },
        version="4.5.9",
    )
    nb = _build_api(client)

    pks = [d.id async for d in nb.dcim.devices.all(limit=10)]

    assert pks == [9]
    # Offset mode does not seed start; only the explicit limit.
    assert client.calls[0]["query"] == {"limit": "10"}


@pytest.mark.asyncio
async def test_explicit_offset_mode_overrides_auto() -> None:
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                ApiResponse(
                    status=200,
                    text='{"count": 1, "next": null, "previous": null, "results": [{"id": 1, "name": "leaf", "url": "https://netbox.example.com/api/dcim/devices/1/"}]}',
                    headers={},
                )
            ]
        },
        version="4.6.0",
    )
    nb = _build_api(client, pagination_mode="offset")

    [d async for d in nb.dcim.devices.all(limit=5)]

    assert client.calls[0]["query"] == {"limit": "5"}


@pytest.mark.asyncio
async def test_env_override_forces_offset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETBOX_SDK_PAGINATION_MODE", "offset")
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                ApiResponse(
                    status=200,
                    text='{"count": 0, "next": null, "previous": null, "results": []}',
                    headers={},
                )
            ]
        },
        version="4.6.0",
    )
    nb = _build_api(client)

    [d async for d in nb.dcim.devices.all(limit=3)]

    assert client.calls[0]["query"] == {"limit": "3"}


@pytest.mark.asyncio
async def test_start_and_offset_are_mutually_exclusive() -> None:
    client = _RecordingClient({}, version="4.6.0")
    nb = _build_api(client)

    with pytest.raises(ValueError, match="mutually exclusive"):
        nb.dcim.devices.all(limit=2, offset=2, start=5)


@pytest.mark.asyncio
async def test_explicit_start_forces_cursor_mode_and_seeds_value() -> None:
    client = _RecordingClient(
        {("GET", "/api/dcim/devices/"): [_devices_response([_device(42)])]},
        version="4.5.9",
    )
    nb = _build_api(client)

    # User passes start=, which forces cursor mode regardless of detected version.
    [d async for d in nb.dcim.devices.all(limit=10, start=42)]

    assert client.calls[0]["query"] == {"start": "42", "limit": "10"}


@pytest.mark.asyncio
async def test_total_falls_back_to_offset_probe_when_count_is_null() -> None:
    """Endpoint.count() must work in cursor mode by probing offset=0 limit=1."""
    client = _RecordingClient(
        {
            ("GET", "/api/dcim/devices/"): [
                # First call: count() probe with offset=0&limit=1.
                ApiResponse(
                    status=200,
                    text='{"count": 17, "next": "https://netbox.example.com/api/dcim/devices/?limit=1&offset=1", "previous": null, "results": [{"id": 1}]}',
                    headers={},
                )
            ]
        },
        version="4.6.0",
    )
    nb = _build_api(client)

    total = await nb.dcim.devices.count()

    assert total == 17
    # The count() path must explicitly request offset=0 even on a 4.6 server.
    assert client.calls[0]["query"] == {"limit": "1", "offset": "0"}


@pytest.mark.asyncio
async def test_cursor_mode_rejects_ordering_filter() -> None:
    client = _RecordingClient({}, version="4.6.0")
    nb = _build_api(client)

    with pytest.raises(ValueError, match="cursor"):
        rs = nb.dcim.devices.filter(ordering="name")
        # First await triggers _initialize_first_page which validates.
        async for _ in rs:
            break
