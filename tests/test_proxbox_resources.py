"""Tests for the dedicated netbox-proxbox resource catalog."""

from __future__ import annotations

import json
from typing import Any

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.proxbox import (
    ProxboxResourceClient,
    build_proxbox_schema_index,
    find_proxbox_resource,
    proxbox_resources,
    register_proxbox_resources,
)
from netbox_sdk.schema import SchemaIndex

pytestmark = pytest.mark.suite_sdk


class _FakeApiClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "query": query,
                "payload": payload,
                "headers": headers,
            }
        )
        return ApiResponse(status=200, text=json.dumps({"ok": True}), headers={})


def test_proxbox_catalog_contains_expected_resource_groups() -> None:
    resources = proxbox_resources()
    keys = {spec.key for spec in resources}

    assert len(resources) == 53
    assert "endpoints/proxmox" in keys
    assert "firewall/rules" in keys
    assert "sdn-vnets" in keys
    assert "deletion-requests" in keys
    assert "sync/schedule" in keys


def test_proxbox_catalog_marks_read_only_resources() -> None:
    deletion_requests = find_proxbox_resource("operations/deletion-requests")
    apply_jobs = find_proxbox_resource("apply-jobs")
    home_view = find_proxbox_resource("views/home")

    assert deletion_requests.supported_actions == ("list", "get")
    assert deletion_requests.read_only is True
    assert apply_jobs.read_only is True
    assert home_view.supported_actions == ("list",)
    assert home_view.read_only is True


def test_proxbox_catalog_limits_settings_writes_to_patch() -> None:
    settings = find_proxbox_resource("settings")

    assert settings.supported_actions == ("list", "get", "patch")
    assert "create" not in settings.supported_actions
    assert "delete" not in settings.supported_actions


def test_register_proxbox_resources_adds_dynamic_operations() -> None:
    index = SchemaIndex({"openapi": "3.0.0", "paths": {}})

    assert register_proxbox_resources(index) is True

    paths = index.resource_paths("plugins", "proxbox/firewall/rules")
    operations = {
        (op.method, op.path)
        for op in index.operations_for("plugins", "proxbox/firewall/rules")
    }

    assert paths is not None
    assert paths.list_path == "/api/plugins/proxbox/firewall/rules/"
    assert paths.detail_path == "/api/plugins/proxbox/firewall/rules/{id}/"
    assert ("POST", "/api/plugins/proxbox/firewall/rules/") in operations
    assert ("PATCH", "/api/plugins/proxbox/firewall/rules/{id}/") in operations
    assert ("DELETE", "/api/plugins/proxbox/firewall/rules/{id}/") in operations


def test_build_proxbox_schema_index_is_proxbox_only() -> None:
    index = build_proxbox_schema_index()

    assert index.groups() == ["plugins"]
    assert "proxbox/endpoints/proxmox" in index.resources("plugins")
    assert "dcim" not in index.groups()


async def test_proxbox_resource_client_resolves_requests() -> None:
    fake = _FakeApiClient()
    client = ProxboxResourceClient.from_client(fake)  # type: ignore[arg-type]

    response = await client.request(
        "firewall/rules",
        "patch",
        object_id=7,
        payload={"enabled": False},
        headers={"X-Test": "yes"},
    )

    assert response.status == 200
    assert fake.calls == [
        {
            "method": "PATCH",
            "path": "/api/plugins/proxbox/firewall/rules/7/",
            "query": {},
            "payload": {"enabled": False},
            "headers": {"X-Test": "yes"},
        }
    ]


async def test_proxbox_resource_client_rejects_unsupported_writes() -> None:
    fake = _FakeApiClient()
    client = ProxboxResourceClient.from_client(fake)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="not supported"):
        await client.request("deletion-requests", "patch", object_id=1, payload={"approved": True})

    assert fake.calls == []
