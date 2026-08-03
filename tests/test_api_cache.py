"""Tests for HTTP response caching, revalidation, and cache file permissions."""

from __future__ import annotations

import json
import os
import stat
import sys
from collections import deque

import pytest

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.http_cache import CachePolicy, build_cache_key

pytestmark = pytest.mark.suite_sdk


def _install_fake_aiohttp(monkeypatch) -> None:
    class _FakeClientSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeClientTimeout:
        def __init__(self, total):
            self.total = total

    class _FakeAiohttp:
        ClientSession = _FakeClientSession
        ClientTimeout = _FakeClientTimeout

    monkeypatch.setitem(sys.modules, "aiohttp", _FakeAiohttp())


def _expire_entry(client: NetBoxApiClient, key: str) -> None:
    path = client._cache._entry_path(key)  # noqa: SLF001
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["fresh_until"] = 0.0
    payload["stale_if_error_until"] = 9999999999.0
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.mark.asyncio
async def test_api_client_serves_fresh_list_response_from_cache(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs)
        return ApiResponse(
            status=200,
            text='{"results": [1]}',
            headers={"ETag": '"abc"'},
        )

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    response1 = await client.request("GET", "/api/dcim/devices/")
    response2 = await client.request("GET", "/api/dcim/devices/")

    assert response1.status == 200
    assert response1.headers["X-NBX-Cache"] == "MISS"
    assert response2.status == 200
    assert response2.headers["X-NBX-Cache"] == "HIT"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_api_client_revalidates_stale_cache_with_etag(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    responses = deque(
        [
            ApiResponse(status=200, text='{"results": [1]}', headers={"ETag": '"abc"'}),
            ApiResponse(status=304, text="", headers={"ETag": '"abc"'}),
        ]
    )
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs)
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    await client.request("GET", "/api/dcim/devices/")
    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token plain-token",
    )
    _expire_entry(client, key)

    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 200
    assert response.text == '{"results": [1]}'
    assert response.headers["X-NBX-Cache"] == "REVALIDATED"
    assert calls[-1]["headers"]["If-None-Match"] == '"abc"'


@pytest.mark.asyncio
async def test_api_client_serves_stale_cache_on_network_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    calls = {"count": 0}

    async def _fake_request_once(self, session, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            return ApiResponse(status=200, text='{"results": [1]}', headers={})
        raise RuntimeError("network down")

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    await client.request("GET", "/api/dcim/devices/")
    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token plain-token",
    )
    _expire_entry(client, key)
    monkeypatch.setattr(
        NetBoxApiClient,
        "_cache_policy",
        lambda self, **kwargs: CachePolicy(fresh_ttl_seconds=0.0, stale_if_error_seconds=300.0),
        raising=True,
    )

    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 200
    assert response.text == '{"results": [1]}'
    assert response.headers["X-NBX-Cache"] == "STALE"


@pytest.mark.asyncio
async def test_api_client_cache_uses_private_permissions(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=200, text='{"results": [1]}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    await client.request("GET", "/api/dcim/devices/")

    entries = list(client._cache.root.glob("*.json"))  # noqa: SLF001
    assert entries
    if os.name != "nt":
        assert stat.S_IMODE(client._cache.root.stat().st_mode) == 0o700  # noqa: SLF001
        assert stat.S_IMODE(entries[0].stat().st_mode) == 0o600


@pytest.mark.asyncio
async def test_api_client_cache_key_scopes_per_call_bearer_override(monkeypatch, tmp_path) -> None:
    """A per-call Authorization override (e.g. MCP forwarding a caller token via
    ``persistent_headers``) must not share a cache entry with a different token,
    even when the client's own config carries no credentials."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(base_url="https://demo.netbox.dev")
    client = NetBoxApiClient(cfg)
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, *, authorization, **kwargs):
        calls.append({"authorization": authorization, **kwargs})
        return ApiResponse(status=200, text='{"results": [1]}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    client.persistent_headers["Authorization"] = "Bearer token-a"
    response_a1 = await client.request("GET", "/api/dcim/devices/")
    response_a2 = await client.request("GET", "/api/dcim/devices/")

    client.persistent_headers["Authorization"] = "Bearer token-b"
    response_b = await client.request("GET", "/api/dcim/devices/")

    assert response_a1.headers["X-NBX-Cache"] == "MISS"
    assert response_a2.headers["X-NBX-Cache"] == "HIT"
    assert response_b.headers["X-NBX-Cache"] == "MISS"
    assert len(calls) == 2
    assert calls[0]["authorization"] == "Bearer token-a"
    assert calls[1]["authorization"] == "Bearer token-b"
    assert calls[0]["headers"]["Authorization"] == "Bearer token-a"
    assert calls[1]["headers"]["Authorization"] == "Bearer token-b"


@pytest.mark.asyncio
async def test_api_client_cache_key_scopes_per_branch_header(monkeypatch, tmp_path) -> None:
    """A same-token GET under two different NetBox Branching schemas
    (``X-NetBox-Branch``) must never collide on the same cached entry — a
    fresh read in branch B must not be served branch A's cached body."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, *, authorization, **kwargs):
        calls.append({"authorization": authorization, **kwargs})
        branch = kwargs["headers"].get("X-NetBox-Branch", "main")
        return ApiResponse(status=200, text=json.dumps({"results": [branch]}), headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    response_a1 = await client.request(
        "GET", "/api/dcim/devices/", headers={"X-NetBox-Branch": "branch-a"}
    )
    response_a2 = await client.request(
        "GET", "/api/dcim/devices/", headers={"X-NetBox-Branch": "branch-a"}
    )
    response_b = await client.request(
        "GET", "/api/dcim/devices/", headers={"X-NetBox-Branch": "branch-b"}
    )

    assert response_a1.headers["X-NBX-Cache"] == "MISS"
    assert response_a2.headers["X-NBX-Cache"] == "HIT"
    assert response_b.headers["X-NBX-Cache"] == "MISS"
    assert len(calls) == 2
    assert json.loads(response_a1.text)["results"] == ["branch-a"]
    assert json.loads(response_a2.text)["results"] == ["branch-a"]
    assert json.loads(response_b.text)["results"] == ["branch-b"]


@pytest.mark.asyncio
async def test_api_client_invalidates_cache_after_successful_write(monkeypatch, tmp_path) -> None:
    """The documented agent read-write-verify sequence must never observe a
    stale cached read after a successful write: a cached detail GET and its
    containing collection GET must both miss immediately after a PATCH."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={}),
            ApiResponse(status=200, text='{"results": [{"id": 5, "name": "old"}]}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={}),
            ApiResponse(status=200, text='{"results": [{"id": 5, "name": "new"}]}', headers={}),
        ]
    )
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs)
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", "/api/dcim/devices/5/")
    list_before = await client.request("GET", "/api/dcim/devices/")
    assert detail_before.headers["X-NBX-Cache"] == "MISS"
    assert list_before.headers["X-NBX-Cache"] == "MISS"

    patch_response = await client.request("PATCH", "/api/dcim/devices/5/", payload={"name": "new"})
    assert patch_response.status == 200

    detail_after = await client.request("GET", "/api/dcim/devices/5/")
    list_after = await client.request("GET", "/api/dcim/devices/")

    assert detail_after.headers["X-NBX-Cache"] == "MISS"
    assert list_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(detail_after.text)["name"] == "new"
    assert json.loads(list_after.text)["results"][0]["name"] == "new"
    assert len(calls) == 5


@pytest.mark.asyncio
async def test_api_client_bulk_write_invalidates_individual_detail_paths(
    monkeypatch, tmp_path
) -> None:
    """Bulk mutations target the list path, never a detail path. Invalidation
    must still purge each affected object's own cached detail GET, derived
    from the ``id`` fields in the bulk payload."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 7, "name": "old"}', headers={}),
            ApiResponse(
                status=200,
                text='[{"id": 7, "name": "new"}]',
                headers={},
            ),
            ApiResponse(status=200, text='{"id": 7, "name": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", "/api/dcim/devices/7/")
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    bulk_response = await client.request(
        "PATCH", "/api/dcim/devices/", payload=[{"id": 7, "name": "new"}]
    )
    assert bulk_response.status == 200

    detail_after = await client.request("GET", "/api/dcim/devices/7/")
    assert detail_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(detail_after.text)["name"] == "new"
