"""Protocol and service tests for semantic plugin tools over MCP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from netbox_mcp.app import create_mcp_server
from netbox_mcp.service import MutationDeniedError, NetBoxMCPService
from netbox_sdk.client import ApiResponse
from netbox_sdk.config import Config
from netbox_sdk.exceptions import ResponseSizeLimitError
from netbox_sdk.plugin_bridge import MAX_INSTANCE_BYTES, PluginBridgeError
from netbox_sdk.schema import SchemaIndex

pytestmark = pytest.mark.suite_mcp

BRIDGE_V1_SAMPLE = Path(__file__).parent / "fixtures" / "plugin_bridge_v1_sample.json"


def _manifest() -> dict[str, Any]:
    payload = json.loads(BRIDGE_V1_SAMPLE.read_text())
    assert isinstance(payload, dict)
    return payload


class _BridgeClient:
    def __init__(self) -> None:
        self.config = Config(base_url="https://netbox.example.com")
        self.persistent_headers: dict[str, str] = {}
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def request_bounded(
        self, method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        self.calls.append(
            {
                "method": method,
                "path": path,
                "max_response_bytes": max_response_bytes,
                **kwargs,
            }
        )
        if path == "/api/plugins/":
            body: object = {"example": "/api/plugins/example/"}
        elif path == "/api/plugins/example/":
            body = {
                "mcp": {
                    "schema_version": "1",
                    "manifest": "/api/plugins/example/mcp/",
                }
            }
        elif path == "/api/plugins/example/mcp/":
            body = _manifest()
        elif method == "GET" and path == "/api/plugins/example/tasks/":
            body = {"count": 0, "tasks": []}
        elif method == "POST" and path == "/api/plugins/example/tasks/":
            body = {"ok": True, "task_id": 17, "message": "queued"}
        else:  # pragma: no cover - unexpected request is a test failure
            raise AssertionError(f"unexpected request: {method} {path}")
        status = 201 if method == "POST" else 200
        return ApiResponse(status=status, text=json.dumps(body), headers={})

    async def close(self) -> None:
        self.closed = True


class _OversizedResponseClient(_BridgeClient):
    async def request_bounded(
        self, method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "GET" and path == "/api/plugins/example/tasks/":
            self.calls.append(
                {
                    "method": method,
                    "path": path,
                    "max_response_bytes": max_response_bytes,
                    **kwargs,
                }
            )
            raise ResponseSizeLimitError(max_response_bytes)
        return await super().request_bounded(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )


class _RedirectingTargetClient(_BridgeClient):
    def __init__(self, status: int) -> None:
        super().__init__()
        self.status = status

    async def request_bounded(
        self, method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if path == "/api/plugins/example/tasks/":
            self.calls.append(
                {
                    "method": method,
                    "path": path,
                    "max_response_bytes": max_response_bytes,
                    **kwargs,
                }
            )
            return ApiResponse(
                status=self.status,
                text="",
                headers={"Location": "https://evil.example/forwarded"},
            )
        return await super().request_bounded(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )


def _service(client: _BridgeClient, *, allow_mutations: bool = False) -> NetBoxMCPService:
    return NetBoxMCPService(
        index=SchemaIndex({"openapi": "3.0.0", "paths": {}}),
        client_factory=lambda _config: client,  # type: ignore[arg-type, return-value]
        config_loader=lambda: Config(base_url="https://netbox.example.com"),
        allow_mutations=allow_mutations,
    )


async def test_plugin_list_tools_returns_structured_semantic_catalog() -> None:
    client = _BridgeClient()

    result = await _service(client).plugin_list_tools(plugin="example")

    assert result["schema_version"] == "1"
    assert [tool["qualified_name"] for tool in result["tools"]] == [
        "example.create_task",
        "example.list_tasks",
    ]
    assert result["tools"][1]["request_path"] == ("/api/plugins/example/tasks/")
    assert client.closed is True


async def test_plugin_read_tool_dispatches_through_configured_sdk_client() -> None:
    client = _BridgeClient()

    result = await _service(client).plugin_call_tool(
        plugin="example", tool="list_tasks", arguments={}
    )

    assert result["status"] == 200
    assert result["body"] == {"count": 0, "tasks": []}
    assert client.calls[-1] == {
        "method": "GET",
        "path": "/api/plugins/example/tasks/",
        "max_response_bytes": MAX_INSTANCE_BYTES,
        "query": {},
        "payload": None,
        "headers": None,
    }


async def test_plugin_write_dry_run_validates_but_never_dispatches_mutation() -> None:
    client = _BridgeClient()

    result = await _service(client).plugin_call_tool(
        plugin="example",
        tool="create_task",
        arguments={"category": "inventory"},
        dry_run=True,
    )

    assert result["dry_run"] is True
    assert result["method"] == "POST"
    assert result["body"] == {"category": "inventory"}
    assert all(call["method"] == "GET" for call in client.calls)


async def test_plugin_write_is_denied_by_default_before_target_dispatch() -> None:
    client = _BridgeClient()

    with pytest.raises(MutationDeniedError):
        await _service(client).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory"},
        )

    assert all(call["method"] == "GET" for call in client.calls)


async def test_plugin_write_dispatches_only_after_explicit_mutation_opt_in() -> None:
    client = _BridgeClient()

    result = await _service(client, allow_mutations=True).plugin_call_tool(
        plugin="example",
        tool="create_task",
        arguments={"category": "inventory"},
    )

    assert result["status"] == 201
    assert result["body"]["task_id"] == 17
    assert client.calls[-1]["method"] == "POST"
    assert client.calls[-1]["payload"] == {"category": "inventory"}


async def test_plugin_head_success_returns_none_without_parsing_or_schema_validation() -> None:
    client = _BridgeClient()
    manifest = _manifest()
    manifest["tools"][0]["method"] = "HEAD"
    original_request = client.request_bounded

    async def head_response(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if path == "/api/plugins/example/mcp/":
            return ApiResponse(status=200, text=json.dumps(manifest), headers={})
        if path == "/api/plugins/example/tasks/":
            assert method == "HEAD"
            return ApiResponse(status=200, text="", headers={"Content-Length": "4096"})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = head_response  # type: ignore[method-assign]

    result = await _service(client).plugin_call_tool(
        plugin="example", tool="list_tasks", arguments={}
    )

    assert result["status"] == 200
    assert result["body"] is None


async def test_plugin_write_204_success_returns_none() -> None:
    client = _BridgeClient()
    original_request = client.request_bounded

    async def no_content_response(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "POST" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=204, text="", headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = no_content_response  # type: ignore[method-assign]

    result = await _service(client, allow_mutations=True).plugin_call_tool(
        plugin="example",
        tool="create_task",
        arguments={"category": "inventory"},
    )

    assert result["status"] == 204
    assert result["body"] is None


async def test_plugin_malformed_response_after_write_reports_unknown_outcome() -> None:
    client = _BridgeClient()
    original_request = client.request_bounded

    async def malformed_response(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "POST" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=201, text="not-json", headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = malformed_response  # type: ignore[method-assign]

    with pytest.raises(
        PluginBridgeError,
        match="write outcome unknown; do not retry blindly",
    ):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory"},
        )


async def test_plugin_non_success_write_response_reports_unknown_outcome() -> None:
    client = _BridgeClient()
    original_request = client.request_bounded

    async def server_error_response(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "POST" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=500, text='{"detail":"failed"}', headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = server_error_response  # type: ignore[method-assign]

    with pytest.raises(
        PluginBridgeError,
        match="write outcome unknown; do not retry blindly.*HTTP 500",
    ):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory"},
        )


async def test_locally_invalid_write_header_is_safe_to_correct_and_retry() -> None:
    client = _BridgeClient()

    with pytest.raises(ValueError, match="Expected header") as exc_info:
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory"},
            header=["missing-delimiter"],
        )

    assert "outcome unknown" not in str(exc_info.value)
    assert all(call["method"] == "GET" for call in client.calls)


async def test_plugin_input_schema_failure_never_reaches_target_endpoint() -> None:
    client = _BridgeClient()

    with pytest.raises(ValueError, match="category"):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example", tool="create_task", arguments={}
        )

    assert all(call["path"] != "/api/plugins/example/tasks/" for call in client.calls)


async def test_canonical_date_time_input_is_enforced_before_dispatch() -> None:
    client = _BridgeClient()

    with pytest.raises(PluginBridgeError, match="date-time"):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory", "scheduled_at": "not-a-date"},
        )

    assert all(call["path"] != "/api/plugins/example/tasks/" for call in client.calls)


async def test_canonical_date_time_accepts_rfc3339_leap_second() -> None:
    client = _BridgeClient()

    result = await _service(client, allow_mutations=True).plugin_call_tool(
        plugin="example",
        tool="create_task",
        arguments={
            "category": "inventory",
            "scheduled_at": "1990-12-31T23:59:60Z",
        },
    )

    assert result["status"] == 201
    assert client.calls[-1]["payload"]["scheduled_at"] == "1990-12-31T23:59:60Z"


@pytest.mark.parametrize(
    "scheduled_at",
    [
        "9999-12-31T23:59:60Z",
        "9999-12-31T23:59:60+23:59",
        "9999-12-31T23:59:59-23:59",
        "0001-01-01T00:00:00+23:59",
        "2026-08-12T12:34:60Z",
        "1990-12-31T23:59:60+01:00",
    ],
)
async def test_invalid_or_overflowing_date_time_is_rejected_before_dispatch(
    scheduled_at: str,
) -> None:
    client = _BridgeClient()

    with pytest.raises(PluginBridgeError, match="date-time"):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={"category": "inventory", "scheduled_at": scheduled_at},
        )

    assert all(call["path"] != "/api/plugins/example/tasks/" for call in client.calls)


@pytest.mark.parametrize(
    "target_ids",
    [
        [0],
        [9223372036854775808],
        [True],
        ["7"],
        [7.5],
        [9007199254740992.0],
        [float("inf")],
        [float("nan")],
        [7, 7.0],
    ],
)
async def test_invalid_integer_identity_is_rejected_before_dispatch(
    target_ids: list[object],
) -> None:
    client = _BridgeClient()

    with pytest.raises(PluginBridgeError):
        await _service(client, allow_mutations=True).plugin_call_tool(
            plugin="example",
            tool="create_task",
            arguments={
                "category": "inventory",
                "target_ids": target_ids,
            },
        )

    assert all(call["path"] != "/api/plugins/example/tasks/" for call in client.calls)


@pytest.mark.parametrize("task_id", [9007199254740991.0, 9223372036854775807])
async def test_lossless_integer_response_is_accepted(task_id: int | float) -> None:
    client = _BridgeClient()
    original_request = client.request_bounded
    body = {
        "count": 1,
        "tasks": [
            {
                "id": task_id,
                "name": "bounded",
                "scheduled_at": None,
                "state": "complete",
            }
        ],
    }

    async def bounded_output(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "GET" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=200, text=json.dumps(body), headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = bounded_output  # type: ignore[method-assign]

    result = await _service(client).plugin_call_tool(
        plugin="example", tool="list_tasks", arguments={}
    )

    assert result["body"]["tasks"][0]["id"] == task_id


@pytest.mark.parametrize(
    "task_id",
    [
        0,
        9223372036854775808,
        True,
        "7",
        7.5,
        9007199254740992.0,
        float("inf"),
        float("nan"),
    ],
)
async def test_invalid_integer_response_is_rejected(task_id: object) -> None:
    client = _BridgeClient()
    original_request = client.request_bounded
    body = {
        "count": 1,
        "tasks": [
            {
                "id": task_id,
                "name": "invalid",
                "scheduled_at": None,
                "state": "complete",
            }
        ],
    }

    async def invalid_numeric_output(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "GET" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=200, text=json.dumps(body), headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = invalid_numeric_output  # type: ignore[method-assign]

    with pytest.raises(PluginBridgeError):
        await _service(client).plugin_call_tool(plugin="example", tool="list_tasks", arguments={})


@pytest.mark.parametrize(
    "scheduled_at",
    [
        "not-a-date",
        "2026-08-12T12:34:60Z",
        "9999-12-31T23:59:60Z",
    ],
)
async def test_canonical_date_time_output_is_enforced(scheduled_at: str) -> None:
    client = _BridgeClient()
    original_request = client.request_bounded
    body = {
        "count": 1,
        "tasks": [
            {
                "id": 1,
                "name": "nightly",
                "scheduled_at": scheduled_at,
                "state": "queued",
            }
        ],
    }

    async def invalid_output(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if method == "GET" and path == "/api/plugins/example/tasks/":
            return ApiResponse(status=200, text=json.dumps(body), headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = invalid_output  # type: ignore[method-assign]

    with pytest.raises(PluginBridgeError, match="date-time"):
        await _service(client).plugin_call_tool(plugin="example", tool="list_tasks", arguments={})


async def test_plugin_success_response_size_is_rejected_before_body_parsing() -> None:
    client = _OversizedResponseClient()

    with pytest.raises(PluginBridgeError, match="size limit"):
        await _service(client).plugin_call_tool(plugin="example", tool="list_tasks", arguments={})


@pytest.mark.parametrize("status", [302, 307])
async def test_plugin_target_redirect_is_rejected_without_following(status: int) -> None:
    client = _RedirectingTargetClient(status)

    with pytest.raises(PluginBridgeError, match="redirect"):
        await _service(client).plugin_call_tool(plugin="example", tool="list_tasks", arguments={})


async def test_plugin_response_is_strict_json_even_without_output_schema() -> None:
    client = _BridgeClient()
    manifest = _manifest()
    manifest["tools"][0].pop("outputSchema")

    original_request = client.request_bounded

    async def response_with_nan(
        method: str, path: str, *, max_response_bytes: int, **kwargs: Any
    ) -> ApiResponse:
        if path == "/api/plugins/example/mcp/":
            return ApiResponse(status=200, text=json.dumps(manifest), headers={})
        if path == "/api/plugins/example/tasks/":
            return ApiResponse(status=200, text='{"count": NaN}', headers={})
        return await original_request(
            method,
            path,
            max_response_bytes=max_response_bytes,
            **kwargs,
        )

    client.request_bounded = response_with_nan  # type: ignore[method-assign]

    with pytest.raises(PluginBridgeError, match="finite JSON"):
        await _service(client).plugin_call_tool(plugin="example", tool="list_tasks", arguments={})


async def test_fastmcp_tool_inventory_stays_stable_and_includes_bridge_tools() -> None:
    server = create_mcp_server(_service(_BridgeClient()))

    before = {tool.name for tool in await server.list_tools()}
    await server.call_tool("plugin_list_tools", {"plugin": "example"})
    after = {tool.name for tool in await server.list_tools()}

    assert {"plugin_list_tools", "plugin_call_tool"} <= before
    assert after == before
