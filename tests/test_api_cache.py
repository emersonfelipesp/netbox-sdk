from __future__ import annotations

import json
import sys
from collections import deque

import pytest

from netbox_cli.api import ApiResponse, NetBoxApiClient
from netbox_cli.config import Config
from netbox_cli.http_cache import CachePolicy, build_cache_key


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
async def test_api_client_serves_fresh_list_response_from_cache(
    monkeypatch, tmp_path
) -> None:
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

    monkeypatch.setattr(
        NetBoxApiClient, "_request_once", _fake_request_once, raising=True
    )

    response1 = await client.request("GET", "/api/dcim/devices/")
    response2 = await client.request("GET", "/api/dcim/devices/")

    assert response1.status == 200
    assert response1.headers["X-NBX-Cache"] == "MISS"
    assert response2.status == 200
    assert response2.headers["X-NBX-Cache"] == "HIT"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_api_client_revalidates_stale_cache_with_etag(
    monkeypatch, tmp_path
) -> None:
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

    monkeypatch.setattr(
        NetBoxApiClient, "_request_once", _fake_request_once, raising=True
    )

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
async def test_api_client_serves_stale_cache_on_network_error(
    monkeypatch, tmp_path
) -> None:
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

    monkeypatch.setattr(
        NetBoxApiClient, "_request_once", _fake_request_once, raising=True
    )

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
        lambda self, **kwargs: CachePolicy(
            fresh_ttl_seconds=0.0, stale_if_error_seconds=300.0
        ),
        raising=True,
    )

    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 200
    assert response.text == '{"results": [1]}'
    assert response.headers["X-NBX-Cache"] == "STALE"
