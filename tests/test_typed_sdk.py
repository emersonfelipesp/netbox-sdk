from __future__ import annotations

import pytest

pytestmark = pytest.mark.suite_sdk

from netbox_sdk import (
    TypedRequestValidationError,
    TypedResponseValidationError,
    UnsupportedNetBoxVersionError,
    load_openapi_schema,
    typed_api,
)
from netbox_sdk.client import ApiResponse, RequestError
from netbox_sdk.typed_runtime import validate_query


def _require_email_validator() -> None:
    pytest.importorskip(
        "email_validator",
        reason="typed generated models require email-validator in the active environment",
    )


def test_versioned_openapi_bundles_are_available() -> None:
    schema_45 = load_openapi_schema(version="4.5")
    schema_44 = load_openapi_schema(version="4.4")
    schema_43 = load_openapi_schema(version="4.3")

    assert str(schema_45["info"]["version"]).startswith("4.5")
    assert str(schema_44["info"]["version"]).startswith("4.4")
    assert "(4.3)" in str(schema_43["info"]["version"])


def test_typed_api_rejects_unsupported_versions() -> None:
    with pytest.raises(UnsupportedNetBoxVersionError):
        typed_api("https://netbox.example.com", token="tok", netbox_version="4.2")


def test_typed_api_selects_versioned_client() -> None:
    _require_email_validator()
    api_45 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5.5")
    api_44 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4.10")
    api_43 = typed_api("https://netbox.example.com", token="tok", netbox_version="4.3.7")

    assert api_45.netbox_version == "4.5"
    assert api_44.netbox_version == "4.4"
    assert api_43.netbox_version == "4.3"
    assert hasattr(api_45.dcim.devices, "create")
    assert hasattr(api_45.ipam.prefixes.available_ips, "create")


@pytest.mark.asyncio
async def test_typed_endpoint_validates_request_before_http_call(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

    async def unexpected_request(*args, **kwargs):
        raise AssertionError("request() should not be called when request validation fails")

    monkeypatch.setattr(api.client, "request", unexpected_request)

    with pytest.raises(TypedRequestValidationError):
        await api.ipam.prefixes.available_ips.create(7, body=[{"prefix_length": "invalid"}])


@pytest.mark.asyncio
async def test_typed_endpoint_validates_response_payload(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.5")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/dcim/devices/123/"
        return ApiResponse(status=200, text='{"id": "bad"}')

    monkeypatch.setattr(api.client, "request", fake_request)

    with pytest.raises(TypedResponseValidationError):
        await api.dcim.devices.get(123)


@pytest.mark.asyncio
async def test_typed_get_returns_none_on_404(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4")

    async def fake_request(method, path, **kwargs):
        return ApiResponse(status=404, text='{"detail":"Not found."}')

    monkeypatch.setattr(api.client, "request", fake_request)

    assert await api.dcim.devices.get(404) is None


@pytest.mark.asyncio
async def test_typed_non_get_endpoint_raises_on_404(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.4")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/ipam/prefixes/404/available-ips/"
        return ApiResponse(status=404, text='{"detail":"Not found."}')

    monkeypatch.setattr(api.client, "request", fake_request)

    with pytest.raises(RequestError):
        await api.ipam.prefixes.available_ips.list(404)


def test_validate_query_preserves_array_parameters() -> None:
    _require_email_validator()
    query = validate_query(
        None,
        {
            "tag": ["core", "edge"],
            "limit": 50,
            "brief": True,
        },
        method="GET",
        path="/api/dcim/devices/",
        version="4.5",
    )

    assert query == {
        "tag": ["core", "edge"],
        "limit": "50",
        "brief": "True",
    }


@pytest.mark.asyncio
async def test_typed_action_endpoint_supports_other_versions(monkeypatch) -> None:
    _require_email_validator()
    api = typed_api("https://netbox.example.com", token="tok", netbox_version="4.3")

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/ipam/prefixes/5/available-ips/"
        return ApiResponse(status=200, text='[{"address":"10.0.0.1/24","family":4}]')

    monkeypatch.setattr(api.client, "request", fake_request)

    result = await api.ipam.prefixes.available_ips.list(5)
    assert result[0].address == "10.0.0.1/24"
