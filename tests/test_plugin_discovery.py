"""Tests for live plugin API discovery and plugin navigation grouping."""

from __future__ import annotations

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.schema import build_schema_index
from netbox_tui.navigation import build_navigation_menus
from netbox_tui.plugin_discovery import (
    discover_plugin_resource_paths,
    enrich_schema_index_with_runtime_resources,
)
from tests.conftest import OPENAPI_PATH

pytestmark = pytest.mark.suite_sdk


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_walks_plugin_roots() -> None:
    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            if method == "OPTIONS":
                return ApiResponse(status=404, text="", headers={})
            assert method == "GET"
            payloads = {
                "/api/plugins/": '{"gpon": "/api/plugins/gpon/"}',
                "/api/plugins/gpon/": (
                    '{"olts": "/api/plugins/gpon/olts/", "onts": "/api/plugins/gpon/onts/"}'
                ),
                "/api/plugins/gpon/olts/": '{"count": 1, "results": [{"id": 1}]}',
                "/api/plugins/gpon/onts/": '{"count": 2, "results": [{"id": 2}]}',
            }
            return ApiResponse(status=200, text=payloads[path], headers={})

    paths = await discover_plugin_resource_paths(_FakeClient())  # type: ignore[arg-type]

    assert paths == [
        ("/api/plugins/gpon/olts/", "/api/plugins/gpon/olts/{id}/"),
        ("/api/plugins/gpon/onts/", "/api/plugins/gpon/onts/{id}/"),
    ]


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_supports_nested_plugin_resources() -> None:
    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            if method == "OPTIONS":
                return ApiResponse(status=404, text="", headers={})
            payloads = {
                ("GET", "/api/plugins/"): '{"proxbox": "/api/plugins/proxbox/"}',
                ("GET", "/api/plugins/proxbox/"): (
                    '{"resources": "/api/plugins/proxbox/resources/"}'
                ),
                ("GET", "/api/plugins/proxbox/resources/"): (
                    '{"clusters": "/api/plugins/proxbox/resources/clusters/"}'
                ),
                ("GET", "/api/plugins/proxbox/resources/clusters/"): (
                    '{"count": 1, "results": [{"id": 1}]}'
                ),
            }
            return ApiResponse(status=200, text=payloads[(method, path)], headers={})

    paths = await discover_plugin_resource_paths(_FakeClient())  # type: ignore[arg-type]

    assert paths == [
        (
            "/api/plugins/proxbox/resources/clusters/",
            "/api/plugins/proxbox/resources/clusters/{id}/",
        ),
    ]


@pytest.mark.asyncio
async def test_enrich_schema_index_with_runtime_resources_adds_object_type_endpoint() -> None:
    class _FakeClient:
        async def request(
            self,
            method: str,
            path: str,
            *,
            query: dict[str, str] | None = None,
        ) -> ApiResponse:
            if method == "GET" and path == "/api/plugins/":
                return ApiResponse(status=200, text="{}", headers={})
            if method == "GET" and path == "/api/core/object-types/":
                return ApiResponse(
                    status=200,
                    text=(
                        '{"count": 1, "next": null, "results": ['
                        '{"public": true, "is_plugin_model": true, '
                        '"rest_api_endpoint": "/api/plugins/custom/widgets/"}'
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
            if method == "OPTIONS" and path == "/api/plugins/custom/widgets/{id}/":
                return ApiResponse(
                    status=200,
                    text='{"actions": {"PATCH": {}, "DELETE": {}}}',
                    headers={"Allow": "GET, PATCH, DELETE, OPTIONS"},
                )
            return ApiResponse(status=404, text="", headers={})

    index = build_schema_index(OPENAPI_PATH)
    index.remove_group_resources("plugins")

    changed = await enrich_schema_index_with_runtime_resources(
        index,
        _FakeClient(),  # type: ignore[arg-type]
    )

    assert changed is True
    paths = index.resource_paths("plugins", "custom/widgets")
    assert paths is not None
    assert paths.list_path == "/api/plugins/custom/widgets/"
    assert paths.detail_path == "/api/plugins/custom/widgets/{id}/"
    assert ("POST", "/api/plugins/custom/widgets/") in {
        (operation.method, operation.path)
        for operation in index.operations_for("plugins", "custom/widgets")
    }
    operations = {
        (operation.method, operation.path)
        for operation in index.operations_for("plugins", "custom/widgets")
    }
    assert ("PATCH", "/api/plugins/custom/widgets/{id}/") in operations
    assert ("DELETE", "/api/plugins/custom/widgets/{id}/") in operations


@pytest.mark.asyncio
async def test_object_type_discovery_skips_non_plugin_public_models() -> None:
    class _FakeClient:
        def __init__(self) -> None:
            self.options_paths: list[str] = []

        async def request(
            self,
            method: str,
            path: str,
            *,
            query: dict[str, str] | None = None,
        ) -> ApiResponse:
            del query
            if method == "GET" and path == "/api/plugins/":
                return ApiResponse(status=200, text="{}", headers={})
            if method == "GET" and path == "/api/core/object-types/":
                return ApiResponse(
                    status=200,
                    text=(
                        '{"count": 2, "next": null, "results": ['
                        '{"public": true, "is_plugin_model": false, '
                        '"rest_api_endpoint": "/api/dcim/devices/"},'
                        '{"public": true, "is_plugin_model": true, '
                        '"rest_api_endpoint": "/api/plugins/custom/widgets/"}'
                        "]}"
                    ),
                    headers={},
                )
            if method == "OPTIONS":
                self.options_paths.append(path)
                return ApiResponse(status=200, text='{"actions": {"GET": {}}}', headers={})
            return ApiResponse(status=404, text="", headers={})

    client = _FakeClient()
    index = build_schema_index(OPENAPI_PATH)
    index.remove_group_resources("plugins")

    changed = await enrich_schema_index_with_runtime_resources(index, client)  # type: ignore[arg-type]

    assert changed is True
    assert "/api/dcim/devices/" not in client.options_paths
    assert "/api/plugins/custom/widgets/" in client.options_paths


def test_build_navigation_menus_groups_plugin_resources_by_plugin_name() -> None:
    index = build_schema_index(OPENAPI_PATH)

    menus = build_navigation_menus(index)
    plugins_menu = next(menu for menu in menus if menu.label == "Plugins")

    assert any(group.label == "Gpon" for group in plugins_menu.groups)
    gpon_group = next(group for group in plugins_menu.groups if group.label == "Gpon")
    labels = [item.label for item in gpon_group.items]
    assert "Olts" in labels
    assert "Onts" in labels
