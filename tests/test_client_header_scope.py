"""Tests for NetBoxApiClient.header_scope concurrency safety."""

import asyncio

import pytest

from netbox_sdk.client import NetBoxApiClient, _scoped_headers
from netbox_sdk.config import Config

pytestmark = pytest.mark.suite_sdk


@pytest.fixture
def config() -> Config:
    return Config(base_url="https://netbox.example.com", token_secret="test-token")


async def test_header_scope_visible_inside_block(config: Config) -> None:
    client = NetBoxApiClient(config)
    try:
        with client.header_scope(**{"X-NetBox-Branch": "feature-x"}):
            assert (_scoped_headers.get() or {}).get("X-NetBox-Branch") == "feature-x"
        assert "X-NetBox-Branch" not in (_scoped_headers.get() or {})
    finally:
        await client.close()


async def test_header_scope_concurrent_tasks_do_not_leak(config: Config) -> None:
    """Concurrent tasks in asyncio.gather must each see only their own headers.

    Previously header_scope mutated a shared self._default_headers dict, so a
    finally block in one coroutine could restore the wrong value after a
    sibling coroutine's scope had overwritten it.
    """
    client = NetBoxApiClient(config)

    async def scoped(branch: str, *, settle: float) -> str | None:
        with client.header_scope(**{"X-NetBox-Branch": branch}):
            await asyncio.sleep(settle)
            return (_scoped_headers.get() or {}).get("X-NetBox-Branch")

    try:
        results = await asyncio.gather(
            scoped("feature-a", settle=0.02),
            scoped("feature-b", settle=0.01),
            scoped("feature-c", settle=0.03),
        )
        assert results == ["feature-a", "feature-b", "feature-c"]
        # No leakage to the parent context.
        assert "X-NetBox-Branch" not in (_scoped_headers.get() or {})
    finally:
        await client.close()


async def test_header_scope_nested_restore(config: Config) -> None:
    client = NetBoxApiClient(config)
    try:
        with client.header_scope(**{"X-A": "1"}):
            with client.header_scope(**{"X-B": "2"}):
                assert _scoped_headers.get() == {"X-A": "1", "X-B": "2"}
            assert _scoped_headers.get() == {"X-A": "1"}
        # Outside any scope the var defaults to None (treated as empty).
        assert (_scoped_headers.get() or {}) == {}
    finally:
        await client.close()


async def test_header_scope_drops_empty_values(config: Config) -> None:
    client = NetBoxApiClient(config)
    try:
        with client.header_scope(**{"X-Real": "yes", "X-Empty": ""}):
            scoped = _scoped_headers.get()
            assert scoped == {"X-Real": "yes"}
    finally:
        await client.close()


async def test_header_scope_merges_into_outgoing_request(
    config: Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`request()` must merge ContextVar headers into the outgoing call.

    Validating the ContextVar alone is not enough: a future refactor that
    skipped the merge inside `request()` would still pass the other tests
    in this module. This test asserts the public behavior end-to-end by
    capturing the headers handed to `_request_once`.
    """
    from netbox_sdk.client import ApiResponse

    captured: list[dict[str, str]] = []

    async def fake_request_once(
        self: NetBoxApiClient, session: object, **kwargs: object
    ) -> ApiResponse:
        headers = kwargs.get("headers") or {}
        assert isinstance(headers, dict)
        captured.append(dict(headers))
        return ApiResponse(status=204, text="", headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", fake_request_once)
    # Disable caching so both requests hit `_request_once` regardless of any
    # entries left over from earlier tests.
    monkeypatch.setattr(NetBoxApiClient, "_cache_policy", lambda *args, **kwargs: None)

    client = NetBoxApiClient(config)
    try:
        with client.header_scope(**{"X-NetBox-Branch": "feature-x"}):
            await client.request("GET", "/api/dcim/devices/")
        await client.request("GET", "/api/dcim/devices/")
    finally:
        await client.close()

    assert captured[0].get("X-NetBox-Branch") == "feature-x"
    assert "X-NetBox-Branch" not in captured[1]
