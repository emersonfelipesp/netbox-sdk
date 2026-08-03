"""Tests for HTTP response caching, revalidation, and cache file permissions."""

from __future__ import annotations

import contextlib
import json
import os
import stat
import sys
import threading
import time
from collections import deque

import pytest

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.http_cache import CachePolicy, HttpCacheStore, build_cache_key

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
async def test_api_client_cache_key_treats_authorization_case_insensitively(
    monkeypatch, tmp_path
) -> None:
    """A caller-supplied lower-case "authorization" header must resolve to the
    same identity as "Authorization" for both the outgoing request and the
    cache key. Without case folding, a plain-dict header merge would treat
    them as two independent headers: the wrong (or missing) credential could
    be used for the cache key while the real one is sent on the wire, letting
    an anonymous or differently-cased later request hit the first caller's
    cached response."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(base_url="https://demo.netbox.dev")
    client = NetBoxApiClient(cfg)
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, *, authorization, **kwargs):
        calls.append({"authorization": authorization, **kwargs})
        return ApiResponse(status=200, text='{"results": [1]}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    response_lower = await client.request(
        "GET", "/api/dcim/devices/", headers={"authorization": "Bearer token-a"}
    )
    response_proper = await client.request(
        "GET", "/api/dcim/devices/", headers={"Authorization": "Bearer token-a"}
    )
    response_anonymous = await client.request("GET", "/api/dcim/devices/")

    assert response_lower.headers["X-NBX-Cache"] == "MISS"
    assert response_proper.headers["X-NBX-Cache"] == "HIT"
    assert response_anonymous.headers["X-NBX-Cache"] == "MISS"
    assert len(calls) == 2
    assert calls[0]["authorization"] == "Bearer token-a"
    assert calls[0]["headers"]["Authorization"] == "Bearer token-a"
    assert "authorization" not in calls[0]["headers"]
    assert calls[1]["authorization"] is None


@pytest.mark.asyncio
async def test_api_client_per_call_authorization_wins_regardless_of_header_casing(
    monkeypatch, tmp_path
) -> None:
    """Precedence among persistent < scoped < per-call Authorization headers
    must hold regardless of which layer uses which case variant. A plain
    dict's update() does not reorder a pre-existing key when a
    same-named-but-differently-cased header from a higher-precedence layer
    is applied -- it only appends genuinely new keys at the end -- so
    merging persistent {"Authorization": ...} then scoped
    {"authorization": ...} then per-call {"Authorization": ...} (same case
    as persistent) would, if Authorization were extracted from the merged
    dict by iteration order instead of resolved explicitly per layer,
    incorrectly let the *scoped* value win over the intended highest-
    precedence per-call value. This exercises every casing permutation
    across all three layers."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(base_url="https://demo.netbox.dev")
    client = NetBoxApiClient(cfg)
    calls: list[dict[str, object]] = []

    async def _fake_request_once(self, session, *, authorization, **kwargs):
        calls.append({"authorization": authorization, **kwargs})
        return ApiResponse(status=200, text="{}", headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    # Each iteration uses a distinct path so the response cache (keyed on
    # path + effective authorization, which is identical across every
    # permutation within a loop) never turns a later iteration into a
    # cache HIT that skips _request_once and leaves `calls` empty.
    casings = ["Authorization", "authorization", "AUTHORIZATION"]
    permutations = [(a, b, c) for a in casings for b in casings for c in casings]
    for index, (persistent_case, scoped_case, call_case) in enumerate(permutations):
        calls.clear()
        client.persistent_headers.clear()
        client.persistent_headers[persistent_case] = "Bearer persistent-token"
        with client.header_scope(**{scoped_case: "Bearer scoped-token"}):
            response = await client.request(
                "GET",
                f"/api/dcim/devices/{index}/",
                headers={call_case: "Bearer call-token"},
            )
        assert response.status == 200
        assert calls[0]["authorization"] == "Bearer call-token", (
            f"persistent={persistent_case!r} scoped={scoped_case!r} call={call_case!r}"
        )

    no_call_permutations = [(a, b) for a in casings for b in casings]
    for index, (persistent_case, scoped_case) in enumerate(no_call_permutations):
        calls.clear()
        client.persistent_headers.clear()
        client.persistent_headers[persistent_case] = "Bearer persistent-token"
        with client.header_scope(**{scoped_case: "Bearer scoped-token"}):
            response = await client.request("GET", f"/api/dcim/interfaces/{index}/")
        assert response.status == 200
        assert calls[0]["authorization"] == "Bearer scoped-token", (
            f"persistent={persistent_case!r} scoped={scoped_case!r}"
        )


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
async def test_api_client_get_in_flight_during_write_does_not_repopulate_cache(
    monkeypatch, tmp_path
) -> None:
    """A GET that captures its cache generation before a concurrent write's
    invalidate_path() lands on the same path — the classic read-before-write,
    write-lands-mid-flight, read-completes-after race — must not resurrect the
    now-stale response it fetched. The in-flight caller still gets its own
    response back (that part of the race is unavoidable), but the response
    must never be persisted, so a subsequent verification read misses and
    fetches the post-write data instead of silently serving the pre-write one.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    path = "/api/dcim/devices/7/"

    async def _fake_get_races_write(self, session, **kwargs):
        # The GET has already captured its cache generation (in _request_impl,
        # before this call); simulate a write landing on the same path while
        # this GET is still in flight, before it returns its own response.
        client._cache.invalidate_path(path)
        return ApiResponse(status=200, text='{"id": 7, "name": "old"}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_get_races_write, raising=True)

    raced_response = await client.request("GET", path)
    assert raced_response.status == 200
    assert raced_response.text == '{"id": 7, "name": "old"}'

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is None  # never persisted despite the 200

    async def _fake_get_fresh(self, session, **kwargs):
        return ApiResponse(status=200, text='{"id": 7, "name": "new"}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_get_fresh, raising=True)
    verification_read = await client.request("GET", path)

    assert verification_read.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(verification_read.text)["name"] == "new"


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


@pytest.mark.asyncio
async def test_api_client_available_ips_write_invalidates_ip_address_collection_cache(
    monkeypatch, tmp_path
) -> None:
    """POST /api/ipam/prefixes/{id}/available-ips/ creates IPAddress objects
    that live under /api/ipam/ip-addresses/, not anything under
    /api/ipam/prefixes/. The default invalidation derivation (exact action
    path + its immediate parent detail path) never touches the
    ip-addresses collection, so a list cached before the action would keep
    serving pre-write data even though a new address now exists."""
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
            ApiResponse(status=200, text='{"count": 0, "results": []}', headers={}),
            ApiResponse(status=201, text='{"id": 9, "address": "10.0.0.1/32"}', headers={}),
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 9, "address": "10.0.0.1/32"}]}',
                headers={},
            ),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    list_before = await client.request("GET", "/api/ipam/ip-addresses/")
    assert list_before.headers["X-NBX-Cache"] == "MISS"

    action_response = await client.request("POST", "/api/ipam/prefixes/5/available-ips/")
    assert action_response.status == 201

    list_after = await client.request("GET", "/api/ipam/ip-addresses/")
    assert list_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(list_after.text)["count"] == 1


@pytest.mark.asyncio
async def test_detail_action_write_invalidates_own_resource_collection_cache(
    monkeypatch, tmp_path
) -> None:
    """A real five-segment mutating detail action must invalidate its own
    resource's collection and filtered-list entries, not only the action path
    and immediate parent detail path."""
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
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 5, "status": "failed"}]}',
                headers={},
            ),
            ApiResponse(status=200, text='{"id": 5, "status": "queued"}', headers={}),
            ApiResponse(
                status=200,
                text='{"count": 0, "results": []}',
                headers={},
            ),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    collection_path = "/api/core/background-tasks/"
    query = {"status": "failed"}
    list_before = await client.request("GET", collection_path, query=query)
    assert list_before.headers["X-NBX-Cache"] == "MISS"

    action_response = await client.request(
        "POST", "/api/core/background-tasks/5/requeue/", payload={}
    )
    assert action_response.status == 200

    list_after = await client.request("GET", collection_path, query=query)
    assert list_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(list_after.text)["count"] == 0


@pytest.mark.asyncio
async def test_api_client_available_asns_write_invalidates_asn_collection_cache(
    monkeypatch, tmp_path
) -> None:
    """POST /api/ipam/asn-ranges/{id}/available-asns/ creates ASN objects
    that live under /api/ipam/asns/, not anything under
    /api/ipam/asn-ranges/. The default invalidation derivation (exact action
    path + its immediate parent detail path) never touches the asns
    collection, so a list cached before the action would keep serving
    pre-write data even though a new ASN now exists."""
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
            ApiResponse(status=200, text='{"count": 0, "results": []}', headers={}),
            ApiResponse(status=201, text='{"id": 9, "asn": 65001}', headers={}),
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 9, "asn": 65001}]}',
                headers={},
            ),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    list_before = await client.request("GET", "/api/ipam/asns/")
    assert list_before.headers["X-NBX-Cache"] == "MISS"

    action_response = await client.request("POST", "/api/ipam/asn-ranges/5/available-asns/")
    assert action_response.status == 201

    list_after = await client.request("GET", "/api/ipam/asns/")
    assert list_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(list_after.text)["count"] == 1


@pytest.mark.asyncio
async def test_api_client_available_asns_write_invalidates_asn_range_collection_cache(
    monkeypatch, tmp_path
) -> None:
    """Allocating an ASN changes the parent ASNRange ``asn_count`` field, so
    cached ASN range lists must be invalidated along with the ASN collection."""
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
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 5, "asn_count": 0}]}',
                headers={},
            ),
            ApiResponse(status=201, text='{"id": 9, "asn": 65001}', headers={}),
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 5, "asn_count": 1}]}',
                headers={},
            ),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    parent_before = await client.request("GET", "/api/ipam/asn-ranges/")
    assert parent_before.headers["X-NBX-Cache"] == "MISS"

    action_response = await client.request("POST", "/api/ipam/asn-ranges/5/available-asns/")
    assert action_response.status == 201

    parent_after = await client.request("GET", "/api/ipam/asn-ranges/")
    assert parent_after.headers["X-NBX-Cache"] == "MISS"
    assert json.loads(parent_after.text)["results"][0]["asn_count"] == 1


@pytest.mark.asyncio
async def test_api_client_available_vlans_write_invalidates_vlan_group_collection_cache(
    monkeypatch, tmp_path
) -> None:
    """Allocating a VLAN changes the parent VLANGroup ``vlan_count`` and
    ``utilization`` fields, so cached VLAN group lists must be invalidated."""
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
            ApiResponse(
                status=200,
                text=('{"count": 1, "results": [{"id": 5, "vlan_count": 0, "utilization": "0%"}]}'),
                headers={},
            ),
            ApiResponse(status=201, text='{"id": 9, "vid": 100}', headers={}),
            ApiResponse(
                status=200,
                text=(
                    '{"count": 1, "results": [{"id": 5, "vlan_count": 1, "utilization": "10%"}]}'
                ),
                headers={},
            ),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    parent_before = await client.request("GET", "/api/ipam/vlan-groups/")
    assert parent_before.headers["X-NBX-Cache"] == "MISS"

    action_response = await client.request("POST", "/api/ipam/vlan-groups/5/available-vlans/")
    assert action_response.status == 201

    parent_after = await client.request("GET", "/api/ipam/vlan-groups/")
    assert parent_after.headers["X-NBX-Cache"] == "MISS"
    updated_group = json.loads(parent_after.text)["results"][0]
    assert updated_group["vlan_count"] == 1
    assert updated_group["utilization"] == "10%"


@pytest.mark.asyncio
async def test_api_client_invalidates_cache_on_write_exception(monkeypatch, tmp_path) -> None:
    """A write whose response never arrives (e.g. the connection drops after
    NetBox already committed the mutation) must still purge related cache
    entries — otherwise a verification read can return the fresh pre-write
    cache entry and encourage an unsafe blind retry."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    responses = deque([ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={})])

    async def _fake_request_once(self, session, **kwargs):
        if responses:
            return responses.popleft()
        raise RuntimeError("connection dropped after commit")

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", "/api/dcim/devices/5/")
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    with pytest.raises(RuntimeError, match="connection dropped"):
        await client.request("PATCH", "/api/dcim/devices/5/", payload={"name": "new"})

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path="/api/dcim/devices/5/",
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is None  # purged despite the ambiguous outcome


@pytest.mark.asyncio
async def test_api_client_write_succeeds_despite_cache_invalidation_failure(
    monkeypatch, tmp_path
) -> None:
    """A cache-index filesystem error while invalidating after a write must
    never be surfaced in place of the write's own confirmed HTTP result —
    that would misreport a successful write as failed."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={})

    def _raise_oserror(self, path, payload):
        raise OSError("disk full")

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)
    monkeypatch.setattr(NetBoxApiClient, "_invalidate_related_cache", _raise_oserror, raising=True)

    response = await client.request("PATCH", "/api/dcim/devices/5/", payload={"name": "new"})

    assert response.status == 200
    assert json.loads(response.text)["name"] == "new"


@pytest.mark.asyncio
async def test_write_invalidation_failure_on_one_path_does_not_skip_the_rest(
    monkeypatch, tmp_path
) -> None:
    """A cache-index failure purging one affected path (e.g. a lock timeout
    on the exact detail path) must not prevent the remaining affected paths
    from being attempted. Invalidating the whole batch inside a single
    try/except means one early failure silently skips every path after it —
    including the containing collection path — while the write is still
    reported as successful, so an immediate list read right after a
    confirmed write could still serve a fresh-looking pre-write cache hit."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    detail_path = "/api/dcim/devices/5/"
    collection_path = "/api/dcim/devices/"

    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={}),
            ApiResponse(status=200, text='{"count": 1, "results": [{"id": 5}]}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    await client.request("GET", detail_path)
    await client.request("GET", collection_path)

    detail_key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=detail_path,
        query=None,
        authorization="Token plain-token",
    )
    collection_key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=collection_path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(detail_key) is not None
    assert client._cache.load(collection_key) is not None

    real_invalidate_path = client._cache.invalidate_path
    invalidated: list[str] = []

    def _flaky_invalidate_path(path: str) -> None:
        if path == detail_path:
            raise OSError("disk full")
        invalidated.append(path)
        real_invalidate_path(path)

    monkeypatch.setattr(client._cache, "invalidate_path", _flaky_invalidate_path, raising=True)

    response = await client.request("PATCH", detail_path, payload={"name": "new"})

    assert response.status == 200
    # The failing path was attempted (and logged), but must not have aborted
    # the rest of the batch.
    assert invalidated == [collection_path]
    assert client._cache.load(collection_key) is None


@pytest.mark.asyncio
async def test_api_client_304_race_with_concurrent_write_refetches_unconditionally(
    monkeypatch, tmp_path
) -> None:
    """A conditional GET evaluated as 304 by NetBox only confirms the
    pre-write ETag matched; if a concurrent write invalidated the path while
    the request was in flight, that 304 can no longer be trusted. The client
    must refetch unconditionally instead of resurrecting the stale cached
    body through refresh()."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    path = "/api/dcim/devices/5/"

    async def _fake_initial(self, session, **kwargs):
        return ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={"ETag": '"abc"'})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_initial, raising=True)
    await client.request("GET", path)

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=path,
        query=None,
        authorization="Token plain-token",
    )
    _expire_entry(client, key)

    call_log: list[dict[str, object]] = []

    async def _fake_304_races_write(self, session, **kwargs):
        call_log.append(kwargs)
        if len(call_log) == 1:
            # A concurrent write invalidates the path while our conditional
            # request is in flight, server-evaluated against the pre-write
            # ETag we sent.
            client._cache.invalidate_path(path)
            return ApiResponse(status=304, text="", headers={"ETag": '"abc"'})
        return ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={"ETag": '"def"'})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_304_races_write, raising=True)

    response = await client.request("GET", path)

    assert len(call_log) == 2  # conditional attempt, then an unconditional refetch
    assert "If-None-Match" not in call_log[1]["headers"]
    assert response.status == 200
    assert json.loads(response.text)["name"] == "new"
    assert response.headers["X-NBX-Cache"] == "MISS"

    loaded = client._cache.load(key)
    assert loaded is not None
    assert json.loads(loaded.text)["name"] == "new"


@pytest.mark.asyncio
async def test_api_client_304_race_recapture_survives_second_concurrent_write(
    monkeypatch, tmp_path
) -> None:
    """If a second concurrent write invalidates the path while the
    unconditional replacement request (triggered by the first race) is still
    in flight, the fenced save must see that second invalidation and skip
    persisting. Recapturing the generation only *after* the replacement
    response arrives would let the now-stale replacement pass the fence and
    be cached as if it were current."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    path = "/api/dcim/devices/5/"

    async def _fake_initial(self, session, **kwargs):
        return ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={"ETag": '"abc"'})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_initial, raising=True)
    await client.request("GET", path)

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=path,
        query=None,
        authorization="Token plain-token",
    )
    _expire_entry(client, key)

    call_log: list[dict[str, object]] = []

    async def _fake_double_race(self, session, **kwargs):
        call_log.append(kwargs)
        if len(call_log) == 1:
            client._cache.invalidate_path(path)  # first concurrent write
            return ApiResponse(status=304, text="", headers={"ETag": '"abc"'})
        # A second concurrent write lands while the unconditional
        # replacement request triggered by the first race is itself in
        # flight.
        client._cache.invalidate_path(path)
        return ApiResponse(status=200, text='{"id": 5, "name": "newer"}', headers={"ETag": '"ghi"'})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_double_race, raising=True)

    response = await client.request("GET", path)

    assert len(call_log) == 2
    assert response.status == 200
    assert json.loads(response.text)["name"] == "newer"  # caller still gets the fresh response

    assert client._cache.load(key) is None  # but never persisted — the second race wasn't lost


@pytest.mark.asyncio
async def test_api_client_invalidates_cache_after_non_2xx_write_response(
    monkeypatch, tmp_path
) -> None:
    """A write that NetBox commits but then answers with a non-2xx status
    (e.g. a 500 raised by post-commit signal/webhook processing) must still
    purge related cache entries — restricting invalidation to confirmed 2xx
    responses left a committed mutation invisible to the cache, so a
    verification read could return the stale pre-write entry and encourage
    an unsafe duplicate retry."""
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
            ApiResponse(status=500, text='{"detail": "post-commit error"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", "/api/dcim/devices/5/")
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    patch_response = await client.request("PATCH", "/api/dcim/devices/5/", payload={"name": "new"})
    assert patch_response.status == 500

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path="/api/dcim/devices/5/",
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is None


@pytest.mark.asyncio
async def test_api_client_write_through_dot_segment_alias_invalidates_canonical_cache(
    monkeypatch, tmp_path
) -> None:
    """A write issued through a dot-segment alias (e.g.
    "/api/dcim/../ipam/prefixes/5/") must invalidate the same cache entry a
    canonical-path read populated. build_url() resolves dot segments via
    urljoin() before the request hits the wire, so the mutation always lands
    on the canonical resource — if cache keys, the generation fence, and
    invalidate_path() used the raw unnormalized alias instead, the canonical
    cached entry would survive the write and a verification read could still
    return stale pre-write data."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    canonical_path = "/api/ipam/prefixes/5/"
    alias_path = "/api/dcim/../ipam/prefixes/5/"

    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "prefix": "old"}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "prefix": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", canonical_path)
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=canonical_path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is not None

    patch_response = await client.request("PATCH", alias_path, payload={"prefix": "new"})
    assert patch_response.status == 200

    assert client._cache.load(key) is None


@pytest.mark.asyncio
async def test_api_client_write_through_percent_encoded_dot_segment_invalidates_canonical_cache(
    monkeypatch, tmp_path
) -> None:
    """Same hazard as the literal-dot-segment alias test above, but for a
    percent-encoded alias (e.g. "/api/dcim/%2e%2e/ipam/prefixes/5/"). aiohttp
    builds its outbound request via yarl.URL(str, encoded=False), which
    percent-decodes each path segment and resolves the resulting dot segments
    before the request hits the wire — so this alias also lands on the
    canonical resource, even though neither "%2e" nor "%2E" is a literal "."
    that urljoin()/posixpath.normpath() alone would catch. If the cache key,
    generation fence, and invalidate_path() used the literal encoded alias
    instead, the canonical cached entry would survive the write."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    canonical_path = "/api/ipam/prefixes/5/"
    alias_path = "/api/dcim/%2e%2e/ipam/prefixes/5/"

    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "prefix": "old"}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "prefix": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", canonical_path)
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=canonical_path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is not None

    patch_response = await client.request("PATCH", alias_path, payload={"prefix": "new"})
    assert patch_response.status == 200

    assert client._cache.load(key) is None


@pytest.mark.asyncio
async def test_api_client_write_through_repeated_slash_alias_invalidates_canonical_cache(
    monkeypatch, tmp_path
) -> None:
    """Same hazard as the dot-segment alias test above, but for a
    repeated-slash alias (e.g. "/api//dcim/devices/5/") that contains no
    literal or percent-encoded dot segment at all. build_url() always calls
    normalized.lstrip("/") before urljoin(), and that merge collapses
    internal "//" runs down to a single "/" even without a dot segment
    present — so this alias also lands on the canonical resource on the
    wire. If _normalize_request_path() only resolved dot segments and left
    repeated slashes alone, the cache key, generation fence, and
    invalidate_path() would all operate on the unnormalized alias while the
    canonical cached entry silently survived the write."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    canonical_path = "/api/dcim/devices/5/"
    alias_path = "/api//dcim/devices/5/"

    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", canonical_path)
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=canonical_path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is not None

    patch_response = await client.request("PATCH", alias_path, payload={"name": "new"})
    assert patch_response.status == 200

    assert client._cache.load(key) is None


@pytest.mark.asyncio
async def test_api_client_write_through_percent_encoded_unreserved_alias_invalidates_canonical_cache(
    monkeypatch, tmp_path
) -> None:
    """A write issued through a percent-encoded-but-not-dot-segment alias
    (e.g. "/api/%64cim/devices/5/", where "%64" decodes to the unreserved
    character "d") must invalidate the same cache entry a canonical-path
    read populated. aiohttp builds its outbound request via
    yarl.URL(str, encoded=False), which percent-decodes every RFC 3986
    "unreserved" character before the request hits the wire, so this alias
    also lands on the canonical resource even though it contains no dot
    segment at all -- the literal-dot-segment and percent-encoded-dot-segment
    tests above do not exercise this path. If _normalize_request_path() only
    resolved dot segments, the canonical cached entry would survive the
    write and a verification read could still return stale pre-write data."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )
    client = NetBoxApiClient(cfg)
    canonical_path = "/api/dcim/devices/5/"
    alias_path = "/api/%64cim/device%73/5/"

    responses = deque(
        [
            ApiResponse(status=200, text='{"id": 5, "name": "old"}', headers={}),
            ApiResponse(status=200, text='{"id": 5, "name": "new"}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once, raising=True)

    detail_before = await client.request("GET", canonical_path)
    assert detail_before.headers["X-NBX-Cache"] == "MISS"

    key = build_cache_key(
        base_url=cfg.base_url or "",
        method="GET",
        path=canonical_path,
        query=None,
        authorization="Token plain-token",
    )
    assert client._cache.load(key) is not None

    patch_response = await client.request("PATCH", alias_path, payload={"name": "new"})
    assert patch_response.status == 200

    assert client._cache.load(key) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("encoded_separator", ["%2F", "%2f", "%5C", "%5c"])
async def test_api_client_rejects_percent_encoded_path_separator_before_cache_or_network(
    monkeypatch, tmp_path, encoded_separator
) -> None:
    """Encoded separators are ambiguous across NetBox/proxy routers and must
    fail before cache lookup, cache mutation, session creation, or dispatch."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)

    cfg = Config(base_url="https://demo.netbox.dev")
    client = NetBoxApiClient(cfg)

    def _unexpected_cache(*args, **kwargs):
        del args, kwargs
        pytest.fail("encoded path separator must be rejected before cache access")

    async def _unexpected_session():
        pytest.fail("encoded path separator must be rejected before transport setup")

    monkeypatch.setattr(client._cache, "path_generation", _unexpected_cache)
    monkeypatch.setattr(client._cache, "load", _unexpected_cache)
    monkeypatch.setattr(client._cache, "save", _unexpected_cache)
    monkeypatch.setattr(client._cache, "invalidate_path", _unexpected_cache)
    monkeypatch.setattr(client, "_get_session", _unexpected_session)

    with pytest.raises(ValueError, match="percent-encoded path separators"):
        await client.request("GET", f"/api/dcim/devices/a{encoded_separator}b/")


def test_api_client_still_canonicalizes_unreserved_percent_encoding(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    client = NetBoxApiClient(Config(base_url="https://demo.netbox.dev"))

    assert client._normalize_request_path("/api/%64cim/device%73/5/") == "/api/dcim/devices/5/"


def test_refresh_skips_persistence_when_generation_advanced_by_concurrent_write(tmp_path) -> None:
    """Mirrors save()'s fencing: a 304 revalidation must not resurrect an
    entry that a concurrent write already purged via invalidate_path()."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    entry = store.save(
        key,
        ApiResponse(status=200, text='{"old": true}', headers={}),
        policy,
        path=path,
        expected_generation=store.path_generation(path),
    )

    stale_generation = store.path_generation(path)
    store.invalidate_path(path)  # concurrent write lands

    refreshed = store.refresh(key, entry, policy, path=path, expected_generation=stale_generation)

    assert refreshed.text == '{"old": true}'  # in-memory result still returned to the caller
    assert store.load(key) is None  # but never persisted — stays purged
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key not in keys


def test_refresh_persists_when_generation_unchanged(tmp_path) -> None:
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    generation = store.path_generation(path)
    entry = store.save(
        key,
        ApiResponse(status=200, text='{"data": true}', headers={}),
        policy,
        path=path,
        expected_generation=generation,
    )

    refreshed = store.refresh(
        key, entry, policy, path=path, expected_generation=store.path_generation(path)
    )

    loaded = store.load(key)
    assert loaded is not None
    assert loaded.text == '{"data": true}'
    assert loaded.fresh_until == refreshed.fresh_until


def test_locked_index_uses_portable_fallback_lock_when_fcntl_unavailable(
    monkeypatch, tmp_path
) -> None:
    """On platforms without fcntl (e.g. Windows), the index lock must not be a
    no-op — that previously let two concurrent saves silently drop each
    other's index entries and reopened the generation-fencing race the lock
    exists to close."""
    import netbox_sdk.http_cache as http_cache_module

    monkeypatch.setattr(http_cache_module, "fcntl", None)

    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"
    policy = CachePolicy()
    original_write = store._write_index_state
    write_started = threading.Event()
    release_write = threading.Event()

    def _slow_write(index_path, generation, keys):
        write_started.set()
        release_write.wait(timeout=5)
        original_write(index_path, generation, keys)

    store._write_index_state = _slow_write  # type: ignore[method-assign]

    thread_a = threading.Thread(
        target=lambda: store.save(
            "key-a", ApiResponse(status=200, text="{}", headers={}), policy, path=path
        )
    )
    thread_a.start()
    assert write_started.wait(timeout=5)

    thread_b = threading.Thread(
        target=lambda: store.save(
            "key-b", ApiResponse(status=200, text="{}", headers={}), policy, path=path
        )
    )
    thread_b.start()
    time.sleep(0.05)
    assert thread_b.is_alive()  # still blocked on the portable lock, not racing ahead

    release_write.set()
    thread_a.join(timeout=5)
    thread_b.join(timeout=5)

    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert sorted(keys) == ["key-a", "key-b"]


def test_portable_lock_raises_timeout_instead_of_silent_corruption(tmp_path) -> None:
    """A lock file left behind by a crashed process must not deadlock the
    portable fallback forever; a bounded timeout raising loudly is strictly
    safer than the previous no-op that corrupted the index silently."""
    store = HttpCacheStore(tmp_path)
    lock_path = tmp_path / "idx-test.json.lock"
    lock_path.touch()  # simulates a stale lock left by a dead process

    with pytest.raises(TimeoutError):
        with store._portable_lock(lock_path, timeout=0.05, poll_interval=0.01):
            pass  # pragma: no cover - must not be reached


def test_portable_lock_reclaims_lock_left_by_dead_process(tmp_path) -> None:
    """A lock file recording a PID that no longer exists (the process crashed
    while holding it) must be reclaimed near-instantly rather than blocking
    every later cacheable request for the full timeout — left unreclaimed, a
    single crash would permanently poison this cache path forever, since
    nothing else ever removes the file."""
    store = HttpCacheStore(tmp_path)
    lock_path = tmp_path / "idx-test.json.lock"
    # A PID vanishingly unlikely to be alive; os.kill(pid, 0) raises
    # ProcessLookupError for it, which _pid_is_alive() treats as dead.
    dead_pid = 999_999
    lock_path.write_text(str(dead_pid), encoding="ascii")

    started = time.monotonic()
    with store._portable_lock(lock_path, timeout=5.0, poll_interval=0.5):
        pass
    elapsed = time.monotonic() - started

    assert elapsed < 1.0  # reclaimed immediately, not after waiting out poll_interval/timeout


def test_portable_lock_does_not_reclaim_lock_held_by_live_process(tmp_path) -> None:
    """A lock file recording the current (definitely alive) process's own PID
    must not be reclaimed out from under it — only a provably dead owner is
    eligible, so this still raises the bounded timeout rather than silently
    stealing a lock a live process holds."""
    store = HttpCacheStore(tmp_path)
    lock_path = tmp_path / "idx-test.json.lock"
    lock_path.write_text(str(os.getpid()), encoding="ascii")

    with pytest.raises(TimeoutError):
        with store._portable_lock(lock_path, timeout=0.05, poll_interval=0.01):
            pass  # pragma: no cover - must not be reached


def test_path_generation_degrades_to_sentinel_when_lock_unavailable(monkeypatch, tmp_path) -> None:
    """When the per-path lock cannot be acquired (e.g. an ambiguous lock file
    that the timeout can never resolve), path_generation() must degrade to the
    _LOCK_UNAVAILABLE_GENERATION sentinel instead of propagating TimeoutError
    — a lock outage must never block the cacheable GET this fence exists to
    protect from ever reaching NetBox."""
    import netbox_sdk.http_cache as http_cache_module

    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"

    @contextlib.contextmanager
    def _always_times_out(self, index_path):
        raise TimeoutError("simulated lock outage")
        yield  # pragma: no cover - unreachable, satisfies generator shape

    monkeypatch.setattr(HttpCacheStore, "_locked_index", _always_times_out)

    assert store.path_generation(path) == http_cache_module._LOCK_UNAVAILABLE_GENERATION


def test_save_and_refresh_degrade_gracefully_when_lock_unavailable(tmp_path) -> None:
    """save() and refresh() must return the in-memory/refreshed entry rather
    than raising when the per-path lock cannot be acquired — a response was
    already received successfully from NetBox, so a caching failure must
    never turn a successful request into a raised exception."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://demo.netbox.dev", method="GET", path=path, query=None, authorization=None
    )

    from netbox_sdk.http_cache import _LOCK_UNAVAILABLE_GENERATION

    entry = store.save(
        key,
        ApiResponse(status=200, text='{"data": true}', headers={}),
        policy,
        path=path,
        expected_generation=_LOCK_UNAVAILABLE_GENERATION,
    )
    assert entry.text == '{"data": true}'
    # Not persisted: the sentinel short-circuits before any index/entry write.
    assert store.load(key) is None

    refreshed = store.refresh(
        key, entry, policy, path=path, expected_generation=_LOCK_UNAVAILABLE_GENERATION
    )
    assert refreshed.text == entry.text
    assert store.load(key) is None

    @contextlib.contextmanager
    def _always_times_out(self, index_path):
        raise TimeoutError("simulated lock outage")
        yield  # pragma: no cover - unreachable, satisfies generator shape

    original_locked_index = HttpCacheStore._locked_index
    HttpCacheStore._locked_index = _always_times_out  # type: ignore[method-assign]
    try:
        entry_no_fence = store.save(
            key, ApiResponse(status=200, text='{"data": true}', headers={}), policy, path=path
        )
        assert entry_no_fence.text == '{"data": true}'
        assert store.load(key) is None

        refreshed_no_fence = store.refresh(key, entry_no_fence, policy, path=path)
        assert refreshed_no_fence.text == entry_no_fence.text
        assert store.load(key) is None
    finally:
        HttpCacheStore._locked_index = original_locked_index  # type: ignore[method-assign]


def test_record_path_index_survives_concurrent_writes_with_locking(tmp_path) -> None:
    """Two concurrent saves for the same path (e.g. two tokens reading it) must
    not lose either other's key from the on-disk index. Without locking, an
    unlocked read-modify-write can drop one key: a later invalidate_path would
    then never purge the dropped entry, leaving it servable as a stale hit."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"
    policy = CachePolicy()
    original_write = store._write_index_state
    write_started = threading.Event()
    release_write = threading.Event()

    def _slow_write(index_path, generation, keys):
        write_started.set()
        release_write.wait(timeout=5)
        original_write(index_path, generation, keys)

    store._write_index_state = _slow_write  # type: ignore[method-assign]

    thread_a = threading.Thread(
        target=lambda: store.save(
            "key-a", ApiResponse(status=200, text="{}", headers={}), policy, path=path
        )
    )
    thread_a.start()
    assert write_started.wait(timeout=5)

    thread_b = threading.Thread(
        target=lambda: store.save(
            "key-b", ApiResponse(status=200, text="{}", headers={}), policy, path=path
        )
    )
    thread_b.start()
    time.sleep(0.05)
    assert thread_b.is_alive()  # still blocked on the lock

    release_write.set()
    thread_a.join(timeout=5)
    thread_b.join(timeout=5)

    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert sorted(keys) == ["key-a", "key-b"]


def test_purge_all_entries_serializes_against_concurrent_path_write(tmp_path) -> None:
    """A selective corruption recovery (``_purge_all_entries``) must never run
    while a *different, healthy* path's ``save()`` is mid-way through its
    index-then-entry write pair. Before the global-guard lock existed,
    ``_purge_all_entries`` deleted files under the cache root without taking
    out any lock, so it could delete another path's just-written index file
    after that path's ``save()`` had registered a new key but before it had
    written the corresponding entry file. The entry file would then land on
    disk unindexed: ``load()`` decides hits by entry-file existence alone,
    so it would be served as a permanently fresh hit that no later
    ``invalidate_path()`` call could ever discover and purge, since the
    index that would have listed it was already gone. This test proves the
    two operations are still strictly ordered under the current selective
    (single corrupted path) recovery: ``_purge_all_entries`` cannot start its
    scan until a concurrent write's entire index+entry pair has finished —
    and, since that other path is healthy, its entry survives the purge
    entirely."""
    store = HttpCacheStore(tmp_path)
    other_path = "/api/dcim/devices/5/"
    corrupted_path = "/api/dcim/sites/9/"
    policy = CachePolicy()

    corrupted_key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=corrupted_path,
        query=None,
        authorization=None,
    )
    store.save(
        corrupted_key,
        ApiResponse(status=200, text="{}", headers={}),
        policy,
        path=corrupted_path,
        expected_generation=store.path_generation(corrupted_path),
    )
    corrupted_index_path = store._index_path_file(corrupted_path)
    corrupted_index_path.write_text("not valid json", encoding="utf-8")

    original_write_entry = store._write_entry
    entry_write_started = threading.Event()
    release_entry_write = threading.Event()

    def _paused_write_entry(path, entry):
        entry_write_started.set()
        release_entry_write.wait(timeout=5)
        original_write_entry(path, entry)

    store._write_entry = _paused_write_entry  # type: ignore[method-assign]

    save_thread = threading.Thread(
        target=lambda: store.save(
            "other-key", ApiResponse(status=200, text="{}", headers={}), policy, path=other_path
        )
    )
    save_thread.start()
    assert entry_write_started.wait(timeout=5)

    # other_path's index file has already been written (registering
    # "other-key") but its entry file has not yet been written — exactly
    # the window the pre-fix race exploited.
    other_index_path = store._index_path_file(other_path)
    assert other_index_path.exists()
    _generation, keys = store._load_index_state_or_none(other_index_path)
    assert keys == ["other-key"]
    assert not store._entry_path("other-key").exists()

    purge_thread = threading.Thread(target=store._purge_all_entries, args=(corrupted_index_path,))
    purge_thread.start()
    time.sleep(0.05)
    assert purge_thread.is_alive()  # blocked on the global guard lock, not racing ahead

    release_entry_write.set()
    save_thread.join(timeout=5)
    purge_thread.join(timeout=5)

    # The corrupted path's own entry is gone, and its index file was reset...
    assert store.load(corrupted_key) is None
    assert not corrupted_index_path.exists()
    # ...but other_path's write, whether it landed before or after the purge
    # pass, was never collaterally wiped: the meaningful assertion here is
    # that the purge thread stayed blocked instead of interleaving mid-pair,
    # and that a healthy, unrelated path is untouched by the recovery.
    assert other_index_path.exists()
    assert store._entry_path("other-key").exists()


def test_save_skips_persistence_when_generation_advanced_by_concurrent_write(tmp_path) -> None:
    """A GET that started before a write must not repopulate the cache after
    the write's invalidate_path() already ran. save() still returns the
    in-memory entry for the immediate caller, but must not write the entry
    file or re-register it in the index once the generation it captured is
    stale."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"
    policy = CachePolicy()

    stale_generation = store.path_generation(path)
    store.invalidate_path(path)  # simulates a write landing while the GET was in flight

    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    entry = store.save(
        key,
        ApiResponse(status=200, text='{"stale": true}', headers={}),
        policy,
        path=path,
        expected_generation=stale_generation,
    )

    assert entry.text == '{"stale": true}'  # immediate caller still gets its response
    assert store.load(key) is None  # but nothing was persisted to disk
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key not in keys


def test_save_persists_when_generation_unchanged(tmp_path) -> None:
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/"
    policy = CachePolicy()

    generation = store.path_generation(path)
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    store.save(
        key,
        ApiResponse(status=200, text='{"fresh": true}', headers={}),
        policy,
        path=path,
        expected_generation=generation,
    )

    loaded = store.load(key)
    assert loaded is not None
    assert loaded.text == '{"fresh": true}'


def test_save_interrupted_after_index_write_leaves_safe_cache_miss(tmp_path) -> None:
    """save() registers the index key before writing the entry file. If the
    process is interrupted between those two steps (simulated here by making
    _write_entry raise), the index must not be left pointing at an orphan
    entry that invalidate_path() can never discover: load() must treat the
    missing entry file as a plain cache miss, never as a hit for stale or
    nonexistent data."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )

    def _crash(entry_path, entry) -> None:
        raise OSError("simulated crash before entry file is written")

    store._write_entry = _crash  # type: ignore[method-assign]

    with pytest.raises(OSError):
        store.save(
            key,
            ApiResponse(status=200, text='{"data": true}', headers={}),
            policy,
            path=path,
            expected_generation=store.path_generation(path),
        )

    # The index may already reference the key (registered before the crash)...
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key in keys
    # ...but load() must never resurrect it, since no entry file exists.
    assert store.load(key) is None

    # A subsequent invalidate_path() for the same path must not fail even
    # though it will try to unlink an entry file that was never created.
    store.invalidate_path(path)
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key not in keys


def test_invalidate_path_purges_stale_entry_when_index_is_corrupted(tmp_path) -> None:
    """Regression: a corrupted per-path index file must not silently defeat
    invalidate_path(). Before this fix, a malformed index degraded to an
    empty (0, []) keys list, so invalidate_path() purged nothing — the entry
    file written before the corruption stayed on disk and, since load()
    decides hits by entry-file existence alone (never index membership),
    kept being served as a fresh hit forever, even after the "invalidating"
    write that was supposed to remove it."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    store.save(
        key,
        ApiResponse(status=200, text='{"stale": true}', headers={}),
        policy,
        path=path,
        expected_generation=store.path_generation(path),
    )
    assert store.load(key) is not None

    store._index_path_file(path).write_text("not valid json", encoding="utf-8")

    store.invalidate_path(path)

    assert store.load(key) is None
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert keys == []


def test_invalidate_path_corrupted_index_spares_unrelated_healthy_path(tmp_path) -> None:
    """The fail-safe fallback recovers only the corrupted path, never an
    unrelated healthy one: a corrupted index cannot tell us which entries it
    registered, so its own entries cannot be trusted, but every other,
    still-parseable index's entries are known-good and must survive. An
    earlier version of this method purged the entire store on any single
    path's corruption, which reopened the generation-fencing race this cache
    exists to close for every other in-flight request touching a healthy
    path (see ``_purge_all_entries``'s docstring)."""
    store = HttpCacheStore(tmp_path)
    corrupted_path = "/api/dcim/devices/5/"
    unrelated_path = "/api/dcim/sites/9/"
    policy = CachePolicy()
    corrupted_key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=corrupted_path,
        query=None,
        authorization=None,
    )
    unrelated_key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=unrelated_path,
        query=None,
        authorization=None,
    )
    store.save(
        corrupted_key,
        ApiResponse(status=200, text='{"a": true}', headers={}),
        policy,
        path=corrupted_path,
        expected_generation=store.path_generation(corrupted_path),
    )
    store.save(
        unrelated_key,
        ApiResponse(status=200, text='{"b": true}', headers={}),
        policy,
        path=unrelated_path,
        expected_generation=store.path_generation(unrelated_path),
    )
    assert store.load(unrelated_key) is not None

    store._index_path_file(corrupted_path).write_text("{not json", encoding="utf-8")

    store.invalidate_path(corrupted_path)

    assert store.load(corrupted_key) is None
    assert store.load(unrelated_key) is not None
    unrelated_index_path = store._index_path_file(unrelated_path)
    _generation, keys = store._load_index_state_or_none(unrelated_index_path)
    assert keys == [unrelated_key]


def test_save_purges_stale_entry_when_racing_a_corrupted_index(tmp_path) -> None:
    """Regression: the corruption-triggered purge must fire from save() and
    refresh() and path_generation(), not only invalidate_path(). Before this
    fix, only invalidate_path() used the corruption-safe loader — save() and
    refresh() still degraded a corrupted index to an empty (0, []) state and
    happily overwrote it with a fresh, valid-looking index containing only
    their own key. That silently "healed" the index file while permanently
    forgetting any key the corrupted index still registered: that key's
    entry file was never purged and never index-discoverable again, yet kept
    being served as a fresh hit by load() (which decides hits by entry-file
    existence alone) forever — even past a later invalidate_path() call for
    the same path, since the index no longer looked corrupted to it.

    Reproduces the exact race: save key A for path P, corrupt P's index,
    then save a different key B for the SAME path P via the ordinary
    fencing flow an unrelated concurrent GET would use. A's entry must be
    gone (purged as a side effect of B's save), proving the purge fired
    inside save() itself."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key_a = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query={"a": "1"},
        authorization=None,
    )
    key_b = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query={"b": "1"},
        authorization=None,
    )
    store.save(
        key_a,
        ApiResponse(status=200, text='{"a": true}', headers={}),
        policy,
        path=path,
        expected_generation=store.path_generation(path),
    )
    assert store.load(key_a) is not None

    store._index_path_file(path).write_text("not valid json", encoding="utf-8")

    store.save(
        key_b,
        ApiResponse(status=200, text='{"b": true}', headers={}),
        policy,
        path=path,
        expected_generation=None,
    )

    assert store.load(key_a) is None
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key_a not in (keys or [])


def test_refresh_interrupted_after_index_write_leaves_safe_cache_miss(tmp_path) -> None:
    """Mirrors test_save_interrupted_after_index_write_leaves_safe_cache_miss
    for refresh(): an interruption between the index write and the entry
    write during a 304 revalidation must degrade to a safe cache miss, not an
    invalidation-invisible orphan entry."""
    store = HttpCacheStore(tmp_path)
    path = "/api/dcim/devices/5/"
    policy = CachePolicy()
    key = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path=path,
        query=None,
        authorization=None,
    )
    entry = store.save(
        key,
        ApiResponse(status=200, text='{"old": true}', headers={}),
        policy,
        path=path,
        expected_generation=store.path_generation(path),
    )
    assert store.load(key) is not None

    # Simulate a crash between the index write and the entry write by first
    # letting invalidate_path() clear both, then re-registering only the
    # index side the way save()/refresh() now do, and making the entry write
    # raise.
    store.invalidate_path(path)

    def _crash(entry_path, refreshed_entry) -> None:
        raise OSError("simulated crash before entry file is written")

    store._write_entry = _crash  # type: ignore[method-assign]

    with pytest.raises(OSError):
        store.refresh(
            key,
            entry,
            policy,
            path=path,
            expected_generation=store.path_generation(path),
        )

    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key in keys
    assert store.load(key) is None

    store.invalidate_path(path)
    _generation, keys = store._load_index_state_or_none(store._index_path_file(path))
    assert key not in keys
