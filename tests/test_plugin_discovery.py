"""Tests for live plugin API discovery and plugin navigation grouping."""

from __future__ import annotations

import pytest

from netbox_cli.api import ApiResponse
from netbox_cli.schema import build_schema_index
from netbox_cli.ui.navigation import build_navigation_menus
from netbox_cli.ui.plugin_discovery import discover_plugin_resource_paths
from tests.conftest import OPENAPI_PATH


@pytest.mark.asyncio
async def test_discover_plugin_resource_paths_walks_plugin_roots() -> None:
    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
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


def test_build_navigation_menus_groups_plugin_resources_by_plugin_name() -> None:
    index = build_schema_index(OPENAPI_PATH)

    menus = build_navigation_menus(index)
    plugins_menu = next(menu for menu in menus if menu.label == "Plugins")

    assert any(group.label == "Gpon" for group in plugins_menu.groups)
    gpon_group = next(group for group in plugins_menu.groups if group.label == "Gpon")
    labels = [item.label for item in gpon_group.items]
    assert "Olts" in labels
    assert "Onts" in labels
