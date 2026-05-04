"""Comprehensive SDK tests verifying sdk as a fully independent package.

All imports in this file come from ``sdk.*`` directly — never via ``netbox_cli.*``.
This ensures that every assertion validates the SDK standalone contract.
"""

from __future__ import annotations

import json
import sys
import time
from collections import deque
from pathlib import Path

import pytest

# All imports from sdk directly — no netbox_cli dependency
from netbox_sdk import (
    ApiResponse,
    Config,
    ConnectionProbe,
    NetBoxApiClient,
    RequestError,
    build_cache_key,
    build_schema_index,
)
from netbox_sdk.config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    cache_dir,
    clear_profile_config,
    config_path,
    is_runtime_config_complete,
    load_profile_config,
    resolved_token,
    save_profile_config,
)
from netbox_sdk.http_cache import CacheEntry, CachePolicy, HttpCacheStore
from netbox_sdk.plugin_discovery import (
    _extract_child_api_paths,
    _is_collection_payload,
    _normalize_api_path,
    _plugin_detail_path,
    discover_object_type_resources,
    discover_plugin_resource_paths,
)
from netbox_sdk.schema import FilterParam
from netbox_sdk.services import (
    ACTION_METHOD_MAP,
    load_json_payload,
    resolve_dynamic_request,
    run_dynamic_command,
)
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk

# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------


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


def _fake_client(base_url: str = "https://netbox.example.com") -> NetBoxApiClient:
    return NetBoxApiClient(Config(base_url=base_url, token_version="v1", token_secret="testtoken"))


# ---------------------------------------------------------------------------
# sdk.config — resolved_token, is_runtime_config_complete, cache_dir, env vars
# ---------------------------------------------------------------------------


def test_resolved_token_v1() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v1", token_secret="mytoken")
    assert resolved_token(cfg) == "mytoken"


def test_resolved_token_v2_assembles_key_secret() -> None:
    cfg = Config(
        base_url="https://nb.example.com",
        token_version="v2",
        token_key="mykey",
        token_secret="mysecret",
    )
    assert resolved_token(cfg) == "nbt_mykey.mysecret"


def test_resolved_token_v2_already_prefixed_key() -> None:
    cfg = Config(
        base_url="https://nb.example.com",
        token_version="v2",
        token_key="nbt_mykey",
        token_secret="mysecret",
    )
    assert resolved_token(cfg) == "nbt_mykey.mysecret"


def test_resolved_token_v2_missing_key_returns_none() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v2", token_secret="mysecret")
    assert resolved_token(cfg) is None


def test_resolved_token_no_secret_returns_none() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v1")
    assert resolved_token(cfg) is None


def test_is_runtime_config_complete_v1_ok() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v1", token_secret="tok")
    assert is_runtime_config_complete(cfg) is True


def test_is_runtime_config_complete_v2_ok() -> None:
    cfg = Config(
        base_url="https://nb.example.com",
        token_version="v2",
        token_key="k",
        token_secret="s",
    )
    assert is_runtime_config_complete(cfg) is True


def test_is_runtime_config_complete_v2_missing_key() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v2", token_secret="s")
    assert is_runtime_config_complete(cfg) is False


def test_is_runtime_config_complete_missing_url() -> None:
    cfg = Config(token_version="v1", token_secret="tok")
    assert is_runtime_config_complete(cfg) is False


def test_is_runtime_config_complete_missing_secret() -> None:
    cfg = Config(base_url="https://nb.example.com", token_version="v1")
    assert is_runtime_config_complete(cfg) is False


def test_cache_dir_is_sibling_of_config_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg_dir = config_path().parent
    assert cache_dir() == cfg_dir / "http-cache"


def test_env_var_overrides_base_url(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_URL", "https://env-netbox.example.com")
    cfg = load_profile_config(DEFAULT_PROFILE)
    assert cfg.base_url == "https://env-netbox.example.com"


def test_env_var_overrides_token_key_and_secret(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_TOKEN_KEY", "envkey")
    monkeypatch.setenv("NETBOX_TOKEN_SECRET", "envsecret")
    cfg = load_profile_config(DEFAULT_PROFILE)
    assert cfg.token_key == "envkey"
    assert cfg.token_secret == "envsecret"


def test_env_var_does_not_override_demo_profile_url(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_URL", "https://wrong.example.com")
    cfg = load_profile_config(DEMO_PROFILE)
    assert cfg.base_url == DEMO_BASE_URL


def test_save_and_load_profile_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg_in = Config(
        base_url="https://nb.example.com",
        token_version="v2",
        token_key="k",
        token_secret="s",
        timeout=15.0,
    )
    save_profile_config(DEFAULT_PROFILE, cfg_in)
    cfg_out = load_profile_config(DEFAULT_PROFILE)
    assert cfg_out.base_url == "https://nb.example.com"
    assert cfg_out.token_key == "k"
    assert cfg_out.token_secret == "s"
    assert cfg_out.timeout == 15.0


def test_clear_profile_config(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    save_profile_config(DEFAULT_PROFILE, Config(base_url="https://a.example.com"))
    save_profile_config(DEMO_PROFILE, Config(base_url=DEMO_BASE_URL, token_secret="tok"))
    clear_profile_config(DEMO_PROFILE)
    stored = json.loads(config_path().read_text(encoding="utf-8"))
    assert DEFAULT_PROFILE in stored["profiles"]
    assert DEMO_PROFILE not in stored["profiles"]


# ---------------------------------------------------------------------------
# sdk.client — POST, PUT, PATCH, DELETE, probe_connection, get_version, graphql
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_client_post_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=201, text='{"id": 1}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.request("POST", "/api/dcim/devices/", payload={"name": "sw01"})

    assert response.status == 201
    assert captured[0]["method"] == "POST"
    assert captured[0]["payload"] == {"name": "sw01"}


@pytest.mark.asyncio
async def test_client_put_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=200, text='{"id": 5}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.request(
        "PUT", "/api/dcim/devices/5/", payload={"name": "sw01", "site": 1}
    )

    assert response.status == 200
    assert captured[0]["method"] == "PUT"
    assert captured[0]["payload"] == {"name": "sw01", "site": 1}


@pytest.mark.asyncio
async def test_client_patch_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=200, text='{"id": 5}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.request("PATCH", "/api/dcim/devices/5/", payload={"name": "sw01-new"})

    assert response.status == 200
    assert captured[0]["method"] == "PATCH"
    assert captured[0]["payload"] == {"name": "sw01-new"}


@pytest.mark.asyncio
async def test_client_delete_request(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=204, text="", headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.request("DELETE", "/api/dcim/devices/5/")

    assert response.status == 204
    assert captured[0]["method"] == "DELETE"


@pytest.mark.asyncio
async def test_client_post_bypasses_cache(monkeypatch, tmp_path) -> None:
    """POST requests must never be cached."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    calls = 0

    async def _fake_request_once(self, session, **kwargs):
        nonlocal calls
        calls += 1
        return ApiResponse(status=201, text='{"id": calls}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    await client.request("POST", "/api/dcim/devices/", payload={"name": "a"})
    await client.request("POST", "/api/dcim/devices/", payload={"name": "a"})

    assert calls == 2  # no caching


@pytest.mark.asyncio
async def test_client_probe_connection_ok(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(
            status=200,
            text="{}",
            headers={"API-Version": "4.2"},
        )

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    probe = await client.probe_connection()

    assert isinstance(probe, ConnectionProbe)
    assert probe.ok is True
    assert probe.status == 200
    assert probe.version == "4.2"
    assert probe.error is None


@pytest.mark.asyncio
async def test_client_probe_connection_forbidden_counts_as_ok(monkeypatch, tmp_path) -> None:
    """403 on probe means URL is valid but token is wrong — still reachable."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=403, text='{"detail": "auth"}', headers={"API-Version": "4.1"})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    probe = await client.probe_connection()

    assert probe.ok is True
    assert probe.status == 403


@pytest.mark.asyncio
async def test_client_probe_connection_network_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()

    async def _fake_request_once(self, session, **kwargs):
        raise ConnectionError("network down")

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    probe = await client.probe_connection()

    assert probe.ok is False
    assert probe.status == 0
    assert "network down" in (probe.error or "")


@pytest.mark.asyncio
async def test_client_get_version_ok(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=200, text="{}", headers={"API-Version": "3.7"})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    version = await client.get_version()
    assert version == "3.7"


@pytest.mark.asyncio
async def test_client_get_version_raises_on_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=503, text="down", headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    with pytest.raises(RequestError) as exc_info:
        await client.get_version()
    assert exc_info.value.response.status == 503


@pytest.mark.asyncio
async def test_client_graphql(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=200, text='{"data": {"devices": []}}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.graphql("{ devices { id name } }")

    assert response.status == 200
    assert captured[0]["method"] == "POST"
    assert captured[0]["path"] == "/api/graphql/"
    payload = captured[0]["payload"]
    assert payload["query"] == "{ devices { id name } }"


@pytest.mark.asyncio
async def test_client_graphql_with_variables(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=200, text='{"data": {}}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    await client.graphql("query($id: Int!) { device(id: $id) { name } }", variables={"id": 1})

    assert captured[0]["payload"]["variables"] == {"id": 1}


@pytest.mark.asyncio
async def test_client_no_token_refresh_callback_by_default(monkeypatch, tmp_path) -> None:
    """Without a callback, demo v1 token expiry returns the 403 unchanged."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="expired",
        demo_username="u",
        demo_password="p",
    )
    client = NetBoxApiClient(cfg)  # no on_token_refresh

    async def _fake_request_once(self, session, **kwargs):
        return ApiResponse(status=403, text='{"detail": "Invalid v1 token"}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await client.request("GET", "/api/dcim/devices/")
    assert response.status == 403  # callback absent → no retry


@pytest.mark.asyncio
async def test_client_token_refresh_callback_invoked(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="expired",
        demo_username="u",
        demo_password="p",
    )
    responses = deque(
        [
            ApiResponse(status=403, text='{"detail": "Invalid v1 token"}', headers={}),
            ApiResponse(status=200, text='{"results": []}', headers={}),
        ]
    )
    calls: list[str] = []

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs["authorization"])
        return responses.popleft()

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    fresh_cfg = Config(base_url=DEMO_BASE_URL, token_version="v1", token_secret="fresh-token")

    def _refresh_callback(config: Config) -> tuple[str | None, Config]:
        return "Token fresh-token", fresh_cfg

    client = NetBoxApiClient(cfg, on_token_refresh=_refresh_callback)
    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 200
    assert calls == ["Token expired", "Token fresh-token"]
    assert client.config.token_secret == "fresh-token"


# ---------------------------------------------------------------------------
# sdk.http_cache — build_cache_key, CacheEntry TTL, HttpCacheStore isolation
# ---------------------------------------------------------------------------


def test_build_cache_key_deterministic() -> None:
    key1 = build_cache_key(
        base_url="https://nb.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query={"limit": "10"},
        authorization="Token abc",
    )
    key2 = build_cache_key(
        base_url="https://nb.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query={"limit": "10"},
        authorization="Token abc",
    )
    assert key1 == key2
    assert len(key1) == 64  # SHA-256 hex


def test_build_cache_key_differs_by_auth() -> None:
    k1 = build_cache_key(
        base_url="https://nb.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token abc",
    )
    k2 = build_cache_key(
        base_url="https://nb.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token xyz",
    )
    assert k1 != k2


def test_build_cache_key_differs_by_method() -> None:
    k_get = build_cache_key(
        base_url="https://nb.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization=None,
    )
    k_post = build_cache_key(
        base_url="https://nb.example.com",
        method="POST",
        path="/api/dcim/devices/",
        query=None,
        authorization=None,
    )
    assert k_get != k_post


def test_cache_entry_is_fresh_before_ttl() -> None:
    now = time.time()
    entry = CacheEntry(
        status=200,
        text="{}",
        headers={},
        created_at=now,
        fresh_until=now + 60,
        stale_if_error_until=now + 300,
    )
    assert entry.is_fresh(now) is True
    assert entry.is_fresh(now + 59) is True
    assert entry.is_fresh(now + 61) is False


def test_cache_entry_can_serve_stale_within_window() -> None:
    now = time.time()
    entry = CacheEntry(
        status=200,
        text="{}",
        headers={},
        created_at=now,
        fresh_until=now - 10,
        stale_if_error_until=now + 300,
    )
    assert entry.is_fresh(now) is False
    assert entry.can_serve_stale(now) is True
    assert entry.can_serve_stale(now + 301) is False


def test_cache_entry_response_parts_injects_cache_status() -> None:
    now = time.time()
    entry = CacheEntry(
        status=200,
        text='{"results": []}',
        headers={"Content-Type": "application/json"},
        created_at=now,
        fresh_until=now + 60,
        stale_if_error_until=now + 300,
    )
    status, text, headers = entry.response_parts(cache_status="HIT")
    assert status == 200
    assert text == '{"results": []}'
    assert headers["X-NBX-Cache"] == "HIT"
    assert headers["Content-Type"] == "application/json"


def test_http_cache_store_save_and_load(tmp_path) -> None:
    store = HttpCacheStore(tmp_path / "cache")
    policy = CachePolicy(fresh_ttl_seconds=60.0, stale_if_error_seconds=300.0)
    response = ApiResponse(status=200, text='{"id": 1}', headers={"ETag": '"v1"'})
    key = "testkey123"

    entry = store.save(key, response, policy)
    assert entry.status == 200
    assert entry.etag == '"v1"'

    loaded = store.load(key)
    assert loaded is not None
    assert loaded.status == 200
    assert loaded.text == '{"id": 1}'


def test_http_cache_store_load_nonexistent_returns_none(tmp_path) -> None:
    store = HttpCacheStore(tmp_path / "cache")
    assert store.load("nonexistent") is None


def test_http_cache_store_refresh_extends_ttl(tmp_path) -> None:
    store = HttpCacheStore(tmp_path / "cache")
    policy = CachePolicy(fresh_ttl_seconds=60.0, stale_if_error_seconds=300.0)
    response = ApiResponse(status=200, text="orig", headers={})
    key = "refresh-test"

    entry = store.save(key, response, policy)
    now = time.time()
    refreshed = store.refresh(key, entry, policy)

    assert refreshed.text == "orig"
    assert refreshed.fresh_until >= now + 59


def test_http_cache_store_corrupted_entry_returns_none(tmp_path) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "badkey.json").write_text("not-json", encoding="utf-8")
    store = HttpCacheStore(cache_dir)
    assert store.load("badkey") is None


# ---------------------------------------------------------------------------
# sdk.schema — operations_for, filter_params, mutations, bundled data path
# ---------------------------------------------------------------------------


def test_schema_operations_for_dcim_devices() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    ops = idx.operations_for("dcim", "devices")
    assert ops  # non-empty
    methods = {op.method for op in ops}
    assert "GET" in methods
    assert all(op.group == "dcim" for op in ops)
    assert all(op.resource == "devices" for op in ops)


def test_schema_operations_for_unknown_returns_empty() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    assert idx.operations_for("nonexistent", "stuff") == []


def test_schema_filter_params_dcim_devices() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    params = idx.filter_params("dcim", "devices")
    assert params  # non-empty
    names = [p.name for p in params]
    # common device filters
    assert "q" in names  # q should be first
    assert params[0].name == "q"
    # all params are FilterParam instances
    assert all(isinstance(p, FilterParam) for p in params)
    # no pagination params
    assert "limit" not in names
    assert "offset" not in names
    assert "format" not in names


def test_schema_filter_params_no_lookup_suffixes() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    params = idx.filter_params("dcim", "devices")
    names = [p.name for p in params]
    # lookup suffixes should be stripped
    assert not any(n.endswith("__ic") for n in names)
    assert not any(n.endswith("__n") for n in names)
    assert not any(n.endswith("__gt") for n in names)


def test_schema_filter_params_unknown_resource() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    assert idx.filter_params("dcim", "nonexistent") == []


def test_schema_add_discovered_resource() -> None:
    idx = build_schema_index(OPENAPI_PATH)

    changed = idx.add_discovered_resource(
        group="plugins",
        resource="myplugin/widgets",
        list_path="/api/plugins/myplugin/widgets/",
        detail_path="/api/plugins/myplugin/widgets/{id}/",
    )
    assert changed is True

    paths = idx.resource_paths("plugins", "myplugin/widgets")
    assert paths is not None
    assert paths.list_path == "/api/plugins/myplugin/widgets/"
    assert paths.detail_path == "/api/plugins/myplugin/widgets/{id}/"

    ops = idx.operations_for("plugins", "myplugin/widgets")
    methods = {op.method for op in ops}
    assert "GET" in methods


def test_schema_add_discovered_resource_with_methods() -> None:
    idx = build_schema_index(OPENAPI_PATH)

    changed = idx.add_discovered_resource(
        group="plugins",
        resource="myplugin/widgets",
        list_path="/api/plugins/myplugin/widgets/",
        detail_path="/api/plugins/myplugin/widgets/{id}/",
        list_methods=("GET", "POST"),
        detail_methods=("GET", "PATCH", "DELETE"),
    )
    assert changed is True

    ops = idx.operations_for("plugins", "myplugin/widgets")
    by_pair = {(op.path, op.method) for op in ops}
    assert ("/api/plugins/myplugin/widgets/", "POST") in by_pair
    assert ("/api/plugins/myplugin/widgets/{id}/", "PATCH") in by_pair
    assert ("/api/plugins/myplugin/widgets/{id}/", "DELETE") in by_pair


def test_schema_add_discovered_resource_idempotent() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    idx.add_discovered_resource(
        group="plugins",
        resource="myplugin/foos",
        list_path="/api/plugins/myplugin/foos/",
    )
    changed = idx.add_discovered_resource(
        group="plugins",
        resource="myplugin/foos",
        list_path="/api/plugins/myplugin/foos/",
    )
    assert changed is False


def test_schema_remove_group_resources() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    idx.add_discovered_resource(
        group="plugins",
        resource="myplugin/bars",
        list_path="/api/plugins/myplugin/bars/",
    )
    assert idx.resources("plugins")

    changed = idx.remove_group_resources("plugins")
    assert changed is True
    assert idx.resources("plugins") == []
    assert idx.resource_paths("plugins", "myplugin/bars") is None


def test_schema_remove_nonexistent_group_returns_false() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    changed = idx.remove_group_resources("nonexistent-group")
    assert changed is False


def test_schema_bundled_data_path_resolves() -> None:
    """Verify the SDK's bundled schema file exists at the correct location."""
    from netbox_sdk.schema import load_openapi_schema

    schema = load_openapi_schema()  # uses Path(__file__).parent — must resolve inside sdk/
    assert isinstance(schema, dict)
    assert "paths" in schema
    assert "info" in schema


def test_schema_resources_sorted() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    resources = idx.resources("dcim")
    assert resources == sorted(resources)


# ---------------------------------------------------------------------------
# sdk.services — load_json_payload, run_dynamic_command, all HTTP methods
# ---------------------------------------------------------------------------


def test_load_json_payload_from_string() -> None:
    payload = load_json_payload('{"name": "sw01", "site": 1}', None)
    assert payload == {"name": "sw01", "site": 1}


def test_load_json_payload_array() -> None:
    payload = load_json_payload('[{"id": 1}, {"id": 2}]', None)
    assert payload == [{"id": 1}, {"id": 2}]


def test_load_json_payload_none_when_no_args() -> None:
    assert load_json_payload(None, None) is None


def test_load_json_payload_raises_when_both_given(tmp_path) -> None:
    with pytest.raises(ValueError, match="not both"):
        load_json_payload('{"a": 1}', str(tmp_path / "file.json"))


def test_load_json_payload_from_file(tmp_path) -> None:
    data = {"device": "sw01", "role": "leaf"}
    f = tmp_path / "payload.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    result = load_json_payload(None, str(f))
    assert result == data


def test_load_json_payload_invalid_json_type() -> None:
    with pytest.raises(ValueError):
        load_json_payload('"just-a-string"', None)


def test_action_method_map_completeness() -> None:
    assert ACTION_METHOD_MAP["list"] == "GET"
    assert ACTION_METHOD_MAP["get"] == "GET"
    assert ACTION_METHOD_MAP["create"] == "POST"
    assert ACTION_METHOD_MAP["update"] == "PUT"
    assert ACTION_METHOD_MAP["patch"] == "PATCH"
    assert ACTION_METHOD_MAP["delete"] == "DELETE"


def test_resolve_dynamic_request_create() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    req = resolve_dynamic_request(
        idx,
        "dcim",
        "devices",
        "create",
        object_id=None,
        query={},
        payload={"name": "sw01"},
    )
    assert req.method == "POST"
    assert req.path == "/api/dcim/devices/"
    assert req.payload == {"name": "sw01"}


def test_resolve_dynamic_request_update() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    req = resolve_dynamic_request(
        idx,
        "dcim",
        "devices",
        "update",
        object_id=7,
        query={},
        payload={"name": "sw01-new"},
    )
    assert req.method == "PUT"
    assert req.path == "/api/dcim/devices/7/"


def test_resolve_dynamic_request_patch() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    req = resolve_dynamic_request(
        idx,
        "dcim",
        "devices",
        "patch",
        object_id=7,
        query={},
        payload={"name": "sw01-patch"},
    )
    assert req.method == "PATCH"
    assert req.path == "/api/dcim/devices/7/"


def test_resolve_dynamic_request_delete() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    req = resolve_dynamic_request(
        idx,
        "dcim",
        "devices",
        "delete",
        object_id=7,
        query={},
        payload=None,
    )
    assert req.method == "DELETE"
    assert req.path == "/api/dcim/devices/7/"


def test_resolve_dynamic_request_unknown_resource() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    with pytest.raises(ValueError, match="Resource not found"):
        resolve_dynamic_request(
            idx,
            "dcim",
            "nonexistent",
            "list",
            object_id=None,
            query={},
            payload=None,
        )


def test_resolve_dynamic_request_detail_without_id() -> None:
    idx = build_schema_index(OPENAPI_PATH)
    with pytest.raises(ValueError, match="requires --id"):
        resolve_dynamic_request(
            idx, "dcim", "devices", "update", object_id=None, query={}, payload=None
        )


@pytest.mark.asyncio
async def test_run_dynamic_command_get(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    idx = build_schema_index(OPENAPI_PATH)
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=200, text='{"count": 0, "results": []}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await run_dynamic_command(
        client,
        idx,
        "dcim",
        "devices",
        "list",
        object_id=None,
        query_pairs=[],
        body_json=None,
        body_file=None,
    )

    assert response.status == 200
    assert captured[0]["method"] == "GET"
    assert captured[0]["path"] == "/api/dcim/devices/"


@pytest.mark.asyncio
async def test_run_dynamic_command_create(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    _install_fake_aiohttp(monkeypatch)
    client = _fake_client()
    idx = build_schema_index(OPENAPI_PATH)
    captured: list[dict] = []

    async def _fake_request_once(self, session, **kwargs):
        captured.append(kwargs)
        return ApiResponse(status=201, text='{"id": 99}', headers={})

    monkeypatch.setattr(NetBoxApiClient, "_request_once", _fake_request_once)

    response = await run_dynamic_command(
        client,
        idx,
        "dcim",
        "devices",
        "create",
        object_id=None,
        query_pairs=[],
        body_json='{"name": "sw99"}',
        body_file=None,
    )

    assert response.status == 201
    assert captured[0]["method"] == "POST"
    assert captured[0]["payload"] == {"name": "sw99"}


# ---------------------------------------------------------------------------
# sdk.plugin_discovery — helpers and error paths
# ---------------------------------------------------------------------------


def test_normalize_api_path_absolute() -> None:
    assert _normalize_api_path("/api/plugins/gpon/olts/") == "/api/plugins/gpon/olts/"


def test_normalize_api_path_adds_trailing_slash() -> None:
    assert _normalize_api_path("/api/plugins/gpon/olts") == "/api/plugins/gpon/olts/"


def test_normalize_api_path_from_full_url() -> None:
    result = _normalize_api_path("https://demo.netbox.dev/api/plugins/gpon/olts/")
    assert result == "/api/plugins/gpon/olts/"


def test_normalize_api_path_rejects_non_api() -> None:
    assert _normalize_api_path("https://example.com/not-api/foo/") is None


def test_normalize_api_path_empty() -> None:
    assert _normalize_api_path("") is None


def test_extract_child_api_paths_from_dict() -> None:
    payload = {"gpon": "/api/plugins/gpon/", "ipam": "/api/ipam/"}
    paths = _extract_child_api_paths(payload)
    assert "/api/plugins/gpon/" in paths
    assert "/api/ipam/" in paths


def test_extract_child_api_paths_nested() -> None:
    payload = {"section": {"subsection": "/api/plugins/foo/bar/"}}
    paths = _extract_child_api_paths(payload)
    assert "/api/plugins/foo/bar/" in paths


def test_extract_child_api_paths_ignores_non_api_strings() -> None:
    payload = {"name": "some-plugin", "url": "https://example.com/notapi/"}
    paths = _extract_child_api_paths(payload)
    assert not any(p for p in paths if "notapi" in p)


def test_is_collection_payload_true() -> None:
    assert _is_collection_payload({"count": 2, "results": []}) is True
    assert _is_collection_payload({"results": []}) is True


def test_is_collection_payload_false() -> None:
    assert _is_collection_payload({"name": "myplugin"}) is False
    assert _is_collection_payload([]) is False
    assert _is_collection_payload("string") is False


def test_plugin_detail_path() -> None:
    assert _plugin_detail_path("/api/plugins/gpon/olts/") == "/api/plugins/gpon/olts/{id}/"


def test_plugin_detail_path_nested_resource() -> None:
    assert (
        _plugin_detail_path("/api/plugins/gpon/olts/nested/")
        == "/api/plugins/gpon/olts/nested/{id}/"
    )


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_direct_sdk_import() -> None:
    """Verify discover_plugin_resource_paths works via sdk import (not netbox_cli)."""

    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            payloads = {
                "/api/plugins/": '{"bgp": "/api/plugins/bgp/"}',
                "/api/plugins/bgp/": '{"sessions": "/api/plugins/bgp/sessions/"}',
                "/api/plugins/bgp/sessions/": '{"count": 3, "results": []}',
            }
            if path not in payloads:
                return ApiResponse(status=404, text="", headers={})
            return ApiResponse(status=200, text=payloads[path], headers={})

    result = await discover_plugin_resource_paths(_FakeClient())  # type: ignore[arg-type]
    assert ("/api/plugins/bgp/sessions/", "/api/plugins/bgp/sessions/{id}/") in result


@pytest.mark.asyncio
async def test_discover_object_type_resources_uses_rest_api_endpoint() -> None:
    class _FakeClient:
        async def request(
            self,
            method: str,
            path: str,
            *,
            query: dict[str, str] | None = None,
        ) -> ApiResponse:
            if method == "GET" and path == "/api/core/object-types/":
                return ApiResponse(
                    status=200,
                    text=json.dumps(
                        {
                            "count": 2,
                            "next": None,
                            "results": [
                                {
                                    "public": True,
                                    "is_plugin_model": True,
                                    "rest_api_endpoint": (
                                        "https://netbox.example.com/api/plugins/custom/widgets/"
                                    ),
                                },
                                {
                                    "public": False,
                                    "rest_api_endpoint": "/api/plugins/private/things/",
                                },
                            ],
                        }
                    ),
                    headers={},
                )
            if method == "OPTIONS" and path == "/api/plugins/custom/widgets/":
                return ApiResponse(
                    status=200,
                    text='{"actions": {"POST": {}}}',
                    headers={"Allow": "GET, POST, OPTIONS"},
                )
            return ApiResponse(status=404, text="", headers={})

    result = await discover_object_type_resources(_FakeClient())  # type: ignore[arg-type]

    assert len(result) == 1
    assert result[0].list_path == "/api/plugins/custom/widgets/"
    assert result[0].detail_path == "/api/plugins/custom/widgets/{id}/"
    assert result[0].list_methods == ("GET", "POST")


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_handles_http_errors() -> None:
    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            if path == "/api/plugins/":
                return ApiResponse(status=200, text='{"bgp": "/api/plugins/bgp/"}', headers={})
            return ApiResponse(status=500, text="error", headers={})

    result = await discover_plugin_resource_paths(_FakeClient())  # type: ignore[arg-type]
    assert result == []


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_skips_network_exceptions() -> None:
    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            raise OSError("connection refused")

    result = await discover_plugin_resource_paths(_FakeClient())  # type: ignore[arg-type]
    assert result == []


# ---------------------------------------------------------------------------
# SDK independence — verify sdk imports never pull from netbox_cli
# ---------------------------------------------------------------------------


def test_sdk_modules_do_not_import_netbox_cli() -> None:
    """No sdk.* module may import from netbox_cli at runtime."""
    import importlib

    sdk_modules = [
        "netbox_sdk",
        "netbox_sdk.config",
        "netbox_sdk.client",
        "netbox_sdk.http_cache",
        "netbox_sdk.schema",
        "netbox_sdk.services",
        "netbox_sdk.plugin_discovery",
    ]
    for mod_name in sdk_modules:
        mod = importlib.import_module(mod_name)
        mod_file = getattr(mod, "__file__", None)
        if mod_file is None:
            continue
        source = Path(mod_file).read_text(encoding="utf-8")
        assert "netbox_cli" not in source, (
            f"{mod_name} contains a 'netbox_cli' import — SDK must be independent"
        )


def test_sdk_all_symbols_are_importable_directly() -> None:
    """Every symbol listed in netbox_sdk.__all__ must be importable from sdk directly."""
    import netbox_sdk

    for name in netbox_sdk.__all__:
        assert hasattr(netbox_sdk, name), f"netbox_sdk.{name} listed in __all__ but not accessible"


def test_sdk_version_defined() -> None:
    import netbox_sdk

    assert netbox_sdk.__version__
    assert isinstance(netbox_sdk.__version__, str)


def test_sdk_py_typed_marker_present() -> None:
    """PEP 561 marker file must exist for type checkers."""
    import netbox_sdk

    sdk_dir = Path(netbox_sdk.__file__).parent  # type: ignore[arg-type]
    assert (sdk_dir / "py.typed").exists()


def test_sdk_bundled_openapi_schema_present() -> None:
    """Bundled OpenAPI schema must ship inside the sdk package."""
    import netbox_sdk

    sdk_dir = Path(netbox_sdk.__file__).parent  # type: ignore[arg-type]
    schema_path = sdk_dir / "reference" / "openapi" / "netbox-openapi.json"
    assert schema_path.exists(), f"Missing bundled schema at {schema_path}"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert "paths" in schema
    assert "info" in schema
