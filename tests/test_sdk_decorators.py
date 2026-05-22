"""Tests for internal SDK response decorators."""

from __future__ import annotations

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.decorators import (
    JsonResponse,
    api_json_response,
    api_raw_response,
    branching_response_error,
)
from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    ContentError,
    RequestError,
)

pytestmark = pytest.mark.suite_sdk


def _response(status: int, text: str) -> ApiResponse:
    return ApiResponse(status=status, text=text)


async def test_api_json_response_decodes_and_checks_type() -> None:
    @api_json_response(expected_type=dict)
    async def _call() -> ApiResponse:
        return _response(200, '{"ok": true}')

    assert await _call() == {"ok": True}


async def test_api_json_response_invalid_json_raises_content_error() -> None:
    @api_json_response()
    async def _call() -> ApiResponse:
        return _response(200, "not-json")

    with pytest.raises(ContentError):
        await _call()


async def test_api_json_response_wrong_type_raises_content_error() -> None:
    @api_json_response(expected_type=dict)
    async def _call() -> ApiResponse:
        return _response(200, "[1, 2]")

    with pytest.raises(ContentError):
        await _call()


async def test_api_json_response_http_error_raises_request_error() -> None:
    @api_json_response()
    async def _call() -> ApiResponse:
        return _response(500, '{"detail": "bad"}')

    with pytest.raises(RequestError):
        await _call()


async def test_api_json_response_supports_dynamic_404_to_none() -> None:
    @api_json_response(none_on_404_kwarg="return_none_on_404")
    async def _call(*, return_none_on_404: bool) -> ApiResponse:
        return _response(404, '{"detail": "missing"}')

    assert await _call(return_none_on_404=True) is None
    with pytest.raises(RequestError):
        await _call(return_none_on_404=False)


async def test_api_json_response_can_include_original_response() -> None:
    @api_json_response(include_response=True)
    async def _call() -> ApiResponse:
        return _response(200, '{"id": 7}')

    decoded = await _call()
    assert isinstance(decoded, JsonResponse)
    assert decoded.response.status == 200
    assert decoded.payload == {"id": 7}


async def test_api_raw_response_returns_text_and_raises_on_error() -> None:
    @api_raw_response()
    async def _ok() -> ApiResponse:
        return _response(200, "plain text")

    @api_raw_response()
    async def _bad() -> ApiResponse:
        return _response(404, "missing")

    assert await _ok() == "plain text"
    with pytest.raises(RequestError):
        await _bad()


async def test_branching_response_error_maps_plugin_and_resource_404() -> None:
    @api_json_response(error_mapper=branching_response_error)
    async def _call(*, resource_op: bool) -> ApiResponse:
        return _response(404, "")

    with pytest.raises(BranchingPluginUnavailableError):
        await _call(resource_op=False)
    with pytest.raises(RequestError):
        await _call(resource_op=True)


async def test_branching_response_error_maps_conflict_payload() -> None:
    @api_json_response(error_mapper=branching_response_error)
    async def _call() -> ApiResponse:
        return _response(409, '{"conflicts": [{"id": 1}]}')

    with pytest.raises(BranchConflictError) as raised:
        await _call()

    assert raised.value.conflicts == [{"id": 1}]
