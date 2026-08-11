"""Tests for the versioned NetBox plugin MCP bridge contract."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest
from pydantic import ValidationError

from netbox_sdk.client import ApiResponse
from netbox_sdk.config import Config
from netbox_sdk.exceptions import ResponseSizeLimitError
from netbox_sdk.plugin_bridge import (
    MAX_MANIFEST_BYTES,
    MAX_PLUGIN_ROOTS,
    MAX_ROOT_DOCUMENT_BYTES,
    PluginBridgeError,
    PluginManifest,
    PluginTool,
    discover_plugin_manifests,
    plugin_tool_request_path,
    validate_plugin_tool_arguments,
)

pytestmark = pytest.mark.suite_sdk


def _tool(
    *,
    name: str = "list_sync_jobs",
    method: str = "GET",
    path: str = "sync/schedule/",
    effect: str = "read",
) -> dict[str, Any]:
    read_only = effect == "read"
    return {
        "name": name,
        "title": name.replace("_", " ").title(),
        "description": "Exercise the existing plugin API endpoint.",
        "method": method,
        "path": path,
        "effect": effect,
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object"},
        "annotations": {
            "readOnlyHint": read_only,
            "destructiveHint": effect == "destructive",
            "idempotentHint": read_only,
            "openWorldHint": False,
        },
    }


def _manifest(*tools: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "plugin": "proxbox",
        "tools": list(tools) or [_tool()],
    }


class _FakeClient:
    def __init__(
        self,
        responses: dict[tuple[str, str], ApiResponse],
        *,
        base_url: str = "https://netbox.example.com",
        delay: float = 0.0,
    ) -> None:
        self.config = Config(base_url=base_url)
        self.responses = responses
        self.calls: list[tuple[str, str]] = []
        self.bounded_limits: list[int] = []
        self.delay = delay

    async def request_bounded(
        self, method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        del kwargs
        if self.delay:
            await asyncio.sleep(self.delay)
        self.calls.append((method, path))
        self.bounded_limits.append(max_response_bytes)
        return self.responses[(method, path)]


class _BoundEnforcingFakeClient(_FakeClient):
    async def request_bounded(
        self, method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        response = await super().request_bounded(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )
        body_size = response.body_size_bytes
        if body_size is None:
            body_size = len(response.text.encode("utf-8"))
        if body_size > max_response_bytes:
            raise ResponseSizeLimitError(max_response_bytes)
        return response


def _response(payload: object, *, status: int = 200) -> ApiResponse:
    return ApiResponse(status=status, text=json.dumps(payload), headers={})


def _discovery_responses(manifest: object | None = None) -> dict[tuple[str, str], ApiResponse]:
    plugin_root: dict[str, object] = {}
    responses = {
        ("GET", "/api/plugins/"): _response(
            {"proxbox": "https://netbox.example.com/api/plugins/proxbox/"}
        ),
    }
    if manifest is not None:
        plugin_root["mcp"] = {
            "schema_version": "1",
            "manifest": "/api/plugins/proxbox/mcp/",
        }
        responses[("GET", "/api/plugins/proxbox/mcp/")] = _response(manifest)
    responses[("GET", "/api/plugins/proxbox/")] = _response(plugin_root)
    return responses


async def test_discovers_explicit_plugin_manifest_and_resolves_local_tool_path() -> None:
    client = _FakeClient(_discovery_responses(_manifest()))

    catalog = await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert catalog.problems == ()
    assert [manifest.plugin for manifest in catalog.manifests] == ["proxbox"]
    tool = catalog.manifests[0].tools[0]
    assert plugin_tool_request_path("proxbox", tool) == ("/api/plugins/proxbox/sync/schedule/")
    assert client.calls == [
        ("GET", "/api/plugins/"),
        ("GET", "/api/plugins/proxbox/"),
        ("GET", "/api/plugins/proxbox/mcp/"),
    ]
    assert client.bounded_limits == [
        MAX_ROOT_DOCUMENT_BYTES,
        MAX_ROOT_DOCUMENT_BYTES,
        MAX_MANIFEST_BYTES,
    ]


async def test_plugin_without_explicit_advertisement_is_not_discovered() -> None:
    catalog = await discover_plugin_manifests(  # type: ignore[arg-type]
        _FakeClient(_discovery_responses())
    )

    assert catalog.manifests == ()
    assert catalog.problems == ()


async def test_specific_plugin_discovery_fails_closed_on_cross_plugin_manifest_link() -> None:
    responses = _discovery_responses(_manifest())
    responses[("GET", "/api/plugins/proxbox/")] = _response(
        {
            "mcp": {
                "schema_version": "1",
                "manifest": "/api/plugins/other/mcp/",
            }
        }
    )

    with pytest.raises(PluginBridgeError, match="advertised manifest path"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(responses), plugin="proxbox"
        )


async def test_all_plugin_discovery_reports_one_bad_manifest_without_hiding_good_plugins() -> None:
    responses = {
        ("GET", "/api/plugins/"): _response(
            {
                "bad": "/api/plugins/bad/",
                "proxbox": "/api/plugins/proxbox/",
            }
        ),
        ("GET", "/api/plugins/bad/"): _response(
            {
                "mcp": {
                    "schema_version": "1",
                    "manifest": "/api/plugins/bad/mcp/",
                }
            }
        ),
        ("GET", "/api/plugins/bad/mcp/"): _response(
            {"schema_version": "99", "plugin": "bad", "tools": []}
        ),
        ("GET", "/api/plugins/proxbox/"): _response(
            {
                "mcp": {
                    "schema_version": "1",
                    "manifest": "/api/plugins/proxbox/mcp/",
                }
            }
        ),
        ("GET", "/api/plugins/proxbox/mcp/"): _response(_manifest()),
    }

    catalog = await discover_plugin_manifests(_FakeClient(responses))  # type: ignore[arg-type]

    assert [manifest.plugin for manifest in catalog.manifests] == ["proxbox"]
    assert len(catalog.problems) == 1
    assert catalog.problems[0].plugin == "bad"
    assert "schema_version" in catalog.problems[0].error


async def test_all_plugin_discovery_isolates_malformed_absolute_url_ports() -> None:
    client = _FakeClient(
        {
            ("GET", "/api/plugins/"): _response(
                {
                    "bad": "https://netbox.example.com:not-a-port/api/plugins/bad/",
                    "proxbox": "/api/plugins/proxbox/",
                }
            ),
            ("GET", "/api/plugins/proxbox/"): _response({}),
        }
    )

    catalog = await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert catalog.manifests == ()
    assert len(catalog.problems) == 1
    assert catalog.problems[0].plugin == "bad"
    assert "URL" in catalog.problems[0].error


async def test_manifest_size_limit_is_checked_before_json_parsing() -> None:
    responses = _discovery_responses(_manifest())
    responses[("GET", "/api/plugins/proxbox/mcp/")] = ApiResponse(
        status=200,
        text="{" + ("x" * MAX_MANIFEST_BYTES),
        headers={},
    )

    with pytest.raises(PluginBridgeError, match="size limit"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(responses), plugin="proxbox"
        )


@pytest.mark.parametrize("status", [302, 307])
async def test_discovery_rejects_manifest_redirects(status: int) -> None:
    responses = _discovery_responses(_manifest())
    responses[("GET", "/api/plugins/proxbox/mcp/")] = ApiResponse(
        status=status,
        text="",
        headers={"Location": "https://evil.example/manifest"},
    )

    with pytest.raises(PluginBridgeError, match=f"HTTP {status}"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(responses), plugin="proxbox"
        )


async def test_prefixed_netbox_base_accepts_and_normalizes_prefixed_links() -> None:
    responses = _discovery_responses(_manifest())
    responses[("GET", "/api/plugins/")] = _response(
        {"proxbox": ("https://netbox.example.com/netbox/api/plugins/proxbox/")}
    )
    responses[("GET", "/api/plugins/proxbox/")] = _response(
        {
            "mcp": {
                "schema_version": "1",
                "manifest": "/netbox/api/plugins/proxbox/mcp/",
            }
        }
    )
    client = _FakeClient(
        responses,
        base_url="https://netbox.example.com/netbox",
    )

    catalog = await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert [manifest.plugin for manifest in catalog.manifests] == ["proxbox"]
    assert client.calls == [
        ("GET", "/api/plugins/"),
        ("GET", "/api/plugins/proxbox/"),
        ("GET", "/api/plugins/proxbox/mcp/"),
    ]


async def test_discovery_rejects_non_finite_and_excessively_nested_json() -> None:
    non_finite = _discovery_responses(_manifest())
    non_finite[("GET", "/api/plugins/proxbox/mcp/")] = ApiResponse(
        status=200,
        text='{"schema_version":"1","plugin":"proxbox","tools":NaN}',
        headers={},
    )
    with pytest.raises(PluginBridgeError, match="finite JSON"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(non_finite), plugin="proxbox"
        )

    nested = _discovery_responses(_manifest())
    nested[("GET", "/api/plugins/proxbox/mcp/")] = ApiResponse(
        status=200,
        text=("[" * 2_000) + ("0") + ("]" * 2_000),
        headers={},
    )
    with pytest.raises(PluginBridgeError, match="valid JSON|nesting"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(nested), plugin="proxbox"
        )


async def test_all_plugin_scan_isolates_nested_json_parser_failure() -> None:
    responses = {
        ("GET", "/api/plugins/"): _response(
            {"bad": "/api/plugins/bad/", "proxbox": "/api/plugins/proxbox/"}
        ),
        ("GET", "/api/plugins/bad/"): ApiResponse(
            status=200,
            text=("[" * 2_000) + "0" + ("]" * 2_000),
            headers={},
        ),
        ("GET", "/api/plugins/proxbox/"): _response({}),
    }

    catalog = await discover_plugin_manifests(  # type: ignore[arg-type]
        _FakeClient(responses)
    )

    assert catalog.manifests == ()
    assert [problem.plugin for problem in catalog.problems] == ["bad"]
    assert "nesting" in catalog.problems[0].error


async def test_all_plugin_discovery_enforces_root_and_catalog_budgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    too_many_roots = {
        f"plugin{index}": f"/api/plugins/plugin{index}/" for index in range(MAX_PLUGIN_ROOTS + 1)
    }
    with pytest.raises(PluginBridgeError, match="plugin root count"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient({("GET", "/api/plugins/"): _response(too_many_roots)})
        )

    monkeypatch.setattr("netbox_sdk.plugin_bridge.MAX_CATALOG_TOOLS", 1)
    two_tools = _manifest(
        _tool(name="first"),
        _tool(name="second", path="sync/other/"),
    )
    with pytest.raises(PluginBridgeError, match="catalog tool count"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(_discovery_responses(two_tools))
        )

    monkeypatch.setattr("netbox_sdk.plugin_bridge.MAX_CATALOG_BYTES", 100)
    with pytest.raises(PluginBridgeError, match="aggregate limit"):
        await discover_plugin_manifests(  # type: ignore[arg-type]
            _FakeClient(_discovery_responses(_manifest()))
        )


async def test_discovery_counts_non_success_bodies_against_aggregate_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _response(
        {
            "bad1": "/api/plugins/bad1/",
            "bad2": "/api/plugins/bad2/",
        }
    )
    first_error = ApiResponse(status=500, text="x" * 40, headers={})
    second_error = ApiResponse(status=503, text="y" * 40, headers={})
    monkeypatch.setattr(
        "netbox_sdk.plugin_bridge.MAX_CATALOG_BYTES",
        len(root.text.encode()) + len(first_error.text.encode()) + 39,
    )
    client = _BoundEnforcingFakeClient(
        {
            ("GET", "/api/plugins/"): root,
            ("GET", "/api/plugins/bad1/"): first_error,
            ("GET", "/api/plugins/bad2/"): second_error,
        }
    )

    with pytest.raises(PluginBridgeError, match="aggregate limit"):
        await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert client.bounded_limits[-1] == 39


async def test_discovery_stream_limit_shrinks_to_remaining_aggregate_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _response({"proxbox": "/api/plugins/proxbox/"})
    plugin_root = _response({"padding": "x" * 100})
    monkeypatch.setattr(
        "netbox_sdk.plugin_bridge.MAX_CATALOG_BYTES",
        len(root.text.encode()) + 10,
    )
    client = _BoundEnforcingFakeClient(
        {
            ("GET", "/api/plugins/"): root,
            ("GET", "/api/plugins/proxbox/"): plugin_root,
        }
    )

    with pytest.raises(PluginBridgeError, match="aggregate limit"):
        await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert client.bounded_limits == [len(root.text.encode()) + 10, 10]


async def test_discovery_charges_predecode_bytes_to_aggregate_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _response({"proxbox": "/api/plugins/proxbox/"})
    root.body_size_bytes = 90
    plugin_root = ApiResponse(
        status=200,
        text="{}",
        headers={},
        body_size_bytes=11,
    )
    monkeypatch.setattr("netbox_sdk.plugin_bridge.MAX_CATALOG_BYTES", 100)
    client = _BoundEnforcingFakeClient(
        {
            ("GET", "/api/plugins/"): root,
            ("GET", "/api/plugins/proxbox/"): plugin_root,
        }
    )

    with pytest.raises(PluginBridgeError, match="aggregate limit"):
        await discover_plugin_manifests(client)  # type: ignore[arg-type]

    assert client.bounded_limits == [100, 10]


async def test_discovery_enforces_one_overall_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("netbox_sdk.plugin_bridge.MAX_DISCOVERY_SECONDS", 0.001)
    client = _FakeClient(_discovery_responses(_manifest()), delay=0.02)

    with pytest.raises(PluginBridgeError, match="deadline"):
        await discover_plugin_manifests(client)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "path",
    [
        "/api/plugins/proxbox/sync/schedule/",
        "../other/",
        "sync/../other/",
        "sync/%2fother/",
        "sync/%5Cother/",
        "https://other.example/api/plugins/proxbox/sync/schedule/",
        "sync\\schedule/",
        "sync/schedule/?now=1",
    ],
)
def test_tool_contract_rejects_non_relative_or_ambiguous_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        PluginTool.model_validate(_tool(path=path))


@pytest.mark.parametrize(
    ("method", "effect"),
    [
        ("POST", "read"),
        ("GET", "write"),
        ("DELETE", "write"),
    ],
)
def test_tool_contract_rejects_method_effect_mismatches(method: str, effect: str) -> None:
    with pytest.raises(ValidationError):
        PluginTool.model_validate(_tool(method=method, effect=effect))


def test_manifest_rejects_duplicate_tool_names() -> None:
    with pytest.raises(ValidationError, match="unique"):
        PluginManifest.model_validate(_manifest(_tool(), _tool()))


def test_tool_contract_rejects_invalid_or_remote_reference_json_schema() -> None:
    invalid = _tool()
    invalid["inputSchema"] = {"type": "not-a-json-schema-type"}
    with pytest.raises(ValidationError, match="valid Draft 2020-12"):
        PluginTool.model_validate(invalid)

    remote = _tool()
    remote["outputSchema"] = {"$ref": "https://other.example/schema.json"}
    with pytest.raises(ValidationError, match="Schema references"):
        PluginTool.model_validate(remote)

    regex = _tool()
    regex["inputSchema"] = {
        "type": "object",
        "properties": {"name": {"type": "string", "pattern": "(a+)+$"}},
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="patterns"):
        PluginTool.model_validate(regex)

    tuple_schema = _tool()
    tuple_schema["inputSchema"] = {
        "type": "object",
        "properties": {
            "values": {
                "type": "array",
                "prefixItems": [{"$ref": "https://other.example/schema.json"}],
            }
        },
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="prefixItems"):
        PluginTool.model_validate(tuple_schema)

    hidden_definition = _tool()
    hidden_definition["outputSchema"] = {
        "type": "object",
        "definitions": {"remote": {"$ref": "https://other.example/schema.json"}},
    }
    with pytest.raises(ValidationError, match="definitions"):
        PluginTool.model_validate(hidden_definition)

    regex_format = _tool()
    regex_format["inputSchema"] = {
        "type": "object",
        "properties": {"expression": {"type": "string", "format": "regex"}},
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="regex"):
        PluginTool.model_validate(regex_format)

    object_uniqueness = _tool()
    object_uniqueness["inputSchema"] = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": "object"},
                "uniqueItems": True,
            }
        },
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="uniqueItems"):
        PluginTool.model_validate(object_uniqueness)

    mixed_scalar_uniqueness = _tool()
    mixed_scalar_uniqueness["inputSchema"] = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {"type": ["string", "integer"]},
                "uniqueItems": True,
            }
        },
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="one explicitly typed scalar"):
        PluginTool.model_validate(mixed_scalar_uniqueness)

    unsupported_format = _tool()
    unsupported_format["inputSchema"] = {
        "type": "object",
        "properties": {"host": {"type": "string", "format": "hostname"}},
        "additionalProperties": False,
    }
    with pytest.raises(ValidationError, match="hostname"):
        PluginTool.model_validate(unsupported_format)


def test_read_tool_contract_rejects_non_query_encodable_inputs() -> None:
    nested = _tool()
    nested["inputSchema"] = {
        "type": "object",
        "properties": {
            "filters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
    }

    with pytest.raises(ValidationError, match="query-encodable"):
        PluginTool.model_validate(nested)


def test_tool_arguments_are_validated_against_advertised_schema() -> None:
    payload = _tool(name="schedule_sync", method="POST", effect="write")
    payload["inputSchema"] = {
        "type": "object",
        "properties": {
            "sync_types": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            }
        },
        "required": ["sync_types"],
        "additionalProperties": False,
    }
    tool = PluginTool.model_validate(payload)

    validate_plugin_tool_arguments(tool, {"sync_types": ["all"]})
    with pytest.raises(PluginBridgeError, match="sync_types"):
        validate_plugin_tool_arguments(tool, {})
    with pytest.raises(PluginBridgeError, match="unexpected"):
        validate_plugin_tool_arguments(tool, {"sync_types": ["all"], "unexpected": True})
