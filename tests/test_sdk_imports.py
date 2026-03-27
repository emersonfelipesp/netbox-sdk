"""Verify that the sdk package exports all expected symbols and works standalone."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.suite_sdk
def test_sdk_top_level_imports() -> None:
    from netbox_sdk import (  # noqa: F401
        ACTION_METHOD_MAP,
        DEFAULT_PROFILE,
        DEMO_BASE_URL,
        DEMO_PROFILE,
        ApiResponse,
        CacheEntry,
        CachePolicy,
        Config,
        ConnectionProbe,
        FilterParam,
        HttpCacheStore,
        NetBoxApiClient,
        Operation,
        RequestError,
        ResolvedRequest,
        ResourcePaths,
        SchemaIndex,
        authorization_header_value,
        build_cache_key,
        build_schema_index,
        cache_dir,
        clear_profile_config,
        config_path,
        discover_plugin_resource_paths,
        is_runtime_config_complete,
        load_config,
        load_json_payload,
        load_openapi_schema,
        load_profile_config,
        normalize_base_url,
        parse_group_resource,
        parse_key_value_pairs,
        resolve_dynamic_request,
        resolved_token,
        run_dynamic_command,
        save_config,
        save_profile_config,
    )


def test_sdk_standalone_client_construction() -> None:
    from netbox_sdk import Config, NetBoxApiClient

    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="abc123testtoken",
    )
    client = NetBoxApiClient(cfg)
    assert client.build_url("/api/dcim/devices/") == "https://netbox.example.com/api/dcim/devices/"
    assert (
        client.build_url("/api/ipam/prefixes/") == "https://netbox.example.com/api/ipam/prefixes/"
    )


def test_sdk_standalone_client_no_callback_by_default() -> None:
    from netbox_sdk import Config, NetBoxApiClient

    cfg = Config(base_url="https://netbox.example.com", token_version="v1", token_secret="tok")
    client = NetBoxApiClient(cfg)
    assert client._on_token_refresh is None


def test_sdk_standalone_client_with_callback() -> None:
    from netbox_sdk import Config, NetBoxApiClient

    def my_refresh(config: Config) -> tuple[str | None, Config]:
        return "Token newtoken", config

    cfg = Config(base_url="https://netbox.example.com", token_version="v1", token_secret="tok")
    client = NetBoxApiClient(cfg, on_token_refresh=my_refresh)
    assert client._on_token_refresh is my_refresh


def test_sdk_schema_index() -> None:
    from netbox_sdk import build_schema_index

    idx = build_schema_index()
    groups = idx.groups()
    assert "dcim" in groups
    assert "ipam" in groups
    assert "circuits" in groups
    resources = idx.resources("dcim")
    assert "devices" in resources


def test_sdk_config_auth_header() -> None:
    from netbox_sdk import Config, authorization_header_value

    cfg_v1 = Config(base_url="https://nb.example.com", token_version="v1", token_secret="mytoken")
    assert authorization_header_value(cfg_v1) == "Token mytoken"

    cfg_v2 = Config(
        base_url="https://nb.example.com",
        token_version="v2",
        token_key="mykey",
        token_secret="mysecret",
    )
    assert authorization_header_value(cfg_v2) == "Bearer nbt_mykey.mysecret"


def test_sdk_resolve_dynamic_request() -> None:
    from netbox_sdk import build_schema_index, resolve_dynamic_request

    idx = build_schema_index()
    req = resolve_dynamic_request(
        idx, "dcim", "devices", "list", object_id=None, query={}, payload=None
    )
    assert req.method == "GET"
    assert req.path == "/api/dcim/devices/"

    req_detail = resolve_dynamic_request(
        idx, "dcim", "devices", "get", object_id=42, query={}, payload=None
    )
    assert req_detail.method == "GET"
    assert req_detail.path == "/api/dcim/devices/42/"
