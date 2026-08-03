"""Tests for the schema-driven NetBox MCP surface and deterministic CLI hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from typer.testing import CliRunner

import netbox_cli as cli
import netbox_mcp
from netbox_mcp.app import (
    AUTH_TOKEN_ENV_VAR,
    BearerTokenMiddleware,
    build_streamable_http_app,
    create_mcp_server,
    is_loopback_host,
)
from netbox_mcp.models import CallInput, GetInput
from netbox_mcp.service import MutationDeniedError, NetBoxMCPService
from netbox_sdk.client import ApiResponse
from netbox_sdk.config import Config
from netbox_sdk.schema import SchemaIndex

pytestmark = pytest.mark.suite_mcp

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def _index() -> SchemaIndex:
    return SchemaIndex(
        {
            "openapi": "3.0.0",
            "paths": {
                "/api/dcim/devices/": {
                    "get": {
                        "operationId": "dcim_devices_list",
                        "summary": "List devices",
                        "parameters": [
                            {
                                "name": "status",
                                "in": "query",
                                "description": "Device status",
                                "schema": {"type": "string", "enum": ["active", "offline"]},
                            }
                        ],
                    },
                    "post": {
                        "operationId": "dcim_devices_create",
                        "summary": "Create device",
                    },
                    "put": {
                        "operationId": "dcim_devices_bulk_update",
                        "summary": "Bulk update devices",
                    },
                    "patch": {
                        "operationId": "dcim_devices_bulk_patch",
                        "summary": "Bulk patch devices",
                    },
                    "delete": {
                        "operationId": "dcim_devices_bulk_delete",
                        "summary": "Bulk delete devices",
                    },
                },
                "/api/dcim/devices/{id}/": {
                    "get": {
                        "operationId": "dcim_devices_retrieve",
                        "summary": "Get device",
                    },
                    "put": {
                        "operationId": "dcim_devices_update",
                        "summary": "Update device",
                    },
                    "patch": {
                        "operationId": "dcim_devices_partial_update",
                        "summary": "Patch device",
                    },
                    "delete": {
                        "operationId": "dcim_devices_destroy",
                        "summary": "Delete device",
                    },
                },
            },
        }
    )


class _MockClient:
    def __init__(self, responses: list[ApiResponse] | None = None) -> None:
        self.responses = responses or [ApiResponse(status=200, text='{"ok": true}', headers={})]
        self.calls: list[dict[str, Any]] = []
        self.persistent_headers: dict[str, str] = {}
        self.closed = False

    async def request(self, method: str, path: str, **kwargs: Any) -> ApiResponse:
        self.calls.append({"method": method, "path": path, **kwargs})
        return self.responses.pop(0)

    async def close(self) -> None:
        self.closed = True


def _service(client: _MockClient, *, allow_mutations: bool = False) -> NetBoxMCPService:
    return NetBoxMCPService(
        index=_index(),
        client_factory=lambda _config: client,  # type: ignore[arg-type, return-value]
        config_loader=lambda: Config(base_url="https://netbox.example.com"),
        allow_mutations=allow_mutations,
    )


def test_tool_argument_models_reject_malformed_input() -> None:
    with pytest.raises(ValidationError):
        GetInput.model_validate({"group": "dcim", "resource": "devices", "id": 0})
    with pytest.raises(ValidationError):
        CallInput.model_validate({"method": "TRACE", "path": "https://other.example/api/"})
    with pytest.raises(ValidationError):
        CallInput.model_validate(
            {"method": "GET", "path": "/api/dcim/devices/", "unexpected": True}
        )


@pytest.mark.parametrize(
    "path",
    [
        "/api/../admin/",
        "/api/dcim/../../admin/",
        "/api/%2e%2e/admin/",
        "/api/%2e%2e%2fadmin/",
        "/api/dcim/%2E%2E/%2E%2E/admin/",
    ],
)
def test_call_input_rejects_path_traversal_outside_api(path: str) -> None:
    """A raw path may pass the literal "/api/" prefix check yet still resolve
    outside it once a reverse proxy or NetBox itself decodes percent-escapes
    and normalizes dot segments server-side. Both literal and percent-encoded
    traversal must be rejected even though this client never decodes/sends a
    normalized path itself."""
    with pytest.raises(ValidationError):
        CallInput.model_validate({"method": "GET", "path": path})


@pytest.mark.parametrize(
    "path",
    [
        "/api/dcim/devices/",
        "/api/dcim/devices/7/",
        "/api/plugins/proxbox/endpoints/proxmox/",
    ],
)
def test_call_input_accepts_ordinary_api_paths(path: str) -> None:
    assert CallInput.model_validate({"method": "GET", "path": path}).path == path


async def test_fastmcp_generated_schema_rejects_invalid_id() -> None:
    server = create_mcp_server(_service(_MockClient()))
    with pytest.raises(Exception, match="greater than 0"):
        await server.call_tool("get", {"group": "dcim", "resource": "devices", "id": 0})


@pytest.mark.parametrize(
    ("method_name", "kwargs"),
    [
        ("create", {"payload": {"name": "leaf01"}}),
        ("update", {"id": 1, "payload": {"name": "leaf01"}}),
        ("patch", {"id": 1, "payload": {"status": "active"}}),
        ("delete", {"id": 1}),
        ("bulk_update", {"payload": [{"id": 1, "name": "leaf01"}]}),
        ("bulk_patch", {"payload": [{"id": 1, "status": "active"}]}),
        ("bulk_delete", {"payload": [{"id": 1}]}),
    ],
)
async def test_mutation_tools_are_denied_by_default(
    method_name: str, kwargs: dict[str, Any]
) -> None:
    service = _service(_MockClient())
    method = getattr(service, method_name)
    with pytest.raises(MutationDeniedError, match="mutations are disabled"):
        await method(group="dcim", resource="devices", **kwargs)


@pytest.mark.parametrize(
    ("method_name", "expected_method", "kwargs"),
    [
        ("create", "POST", {"payload": {"name": "leaf01"}}),
        ("update", "PUT", {"id": 1, "payload": {"name": "leaf01"}}),
        ("patch", "PATCH", {"id": 1, "payload": {"status": "active"}}),
        ("delete", "DELETE", {"id": 1}),
        ("bulk_update", "PUT", {"payload": [{"id": 1, "name": "leaf01"}]}),
        ("bulk_patch", "PATCH", {"payload": [{"id": 1, "status": "active"}]}),
        ("bulk_delete", "DELETE", {"payload": [{"id": 1}]}),
    ],
)
async def test_mutation_tools_execute_only_after_opt_in(
    method_name: str, expected_method: str, kwargs: dict[str, Any]
) -> None:
    client = _MockClient()
    service = _service(client, allow_mutations=True)
    method = getattr(service, method_name)
    response = await method(group="dcim", resource="devices", **kwargs)
    assert response["status"] == 200
    assert len(client.calls) == 1
    assert client.calls[0]["method"] == expected_method


async def test_dry_run_never_constructs_client_and_returns_resolved_request() -> None:
    def _fail_client(_config: object) -> Any:
        pytest.fail("dry-run must not construct a NetBox API client")

    service = NetBoxMCPService(
        index=_index(),
        client_factory=_fail_client,  # type: ignore[arg-type]
        allow_mutations=False,
    )
    preview = await service.patch(
        group="dcim",
        resource="devices",
        id=42,
        payload={"status": "active"},
        dry_run=True,
    )
    assert preview == {
        "dry_run": True,
        "method": "PATCH",
        "path": "/api/dcim/devices/42/",
        "query": {},
        "body": {"status": "active"},
        "notice": preview["notice"],
    }
    assert "not server-side validation" in preview["notice"]


async def test_read_tools_and_local_filters_use_schema_and_mock_client() -> None:
    client = _MockClient(
        [
            ApiResponse(
                status=200,
                text='{"count": 1, "results": [{"id": 1, "name": "leaf01"}]}',
                headers={"ETag": '"list"'},
            ),
            ApiResponse(
                status=200,
                text='{"id": 1, "name": "leaf01"}',
                headers={"ETag": '"detail"'},
            ),
        ]
    )
    service = _service(client)

    listed = await service.list(group="dcim", resource="devices", query=["status=active"])
    fetched = await service.get(group="dcim", resource="devices", id=1)
    filters = service.filters(group="dcim", resource="devices")

    assert listed["body"]["results"][0]["name"] == "leaf01"
    assert fetched["body"]["id"] == 1
    assert filters["filters"][0]["name"] == "status"
    assert client.calls[0]["query"] == {"status": "active"}


async def test_raw_call_rejects_writes_until_mutations_are_enabled() -> None:
    denied_client = _MockClient()
    denied = _service(denied_client)
    with pytest.raises(MutationDeniedError, match="mutations are disabled"):
        await denied.call(
            method="POST",
            path="/api/dcim/devices/",
            payload={"name": "leaf01"},
        )
    assert denied_client.calls == []

    allowed_client = _MockClient()
    allowed = _service(allowed_client, allow_mutations=True)
    response = await allowed.call(
        method="POST",
        path="/api/dcim/devices/",
        payload={"name": "leaf01"},
    )
    assert response["status"] == 200
    assert allowed_client.calls[0]["method"] == "POST"


async def test_mcp_introspection_matches_cli_json_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    index = _index()
    service = NetBoxMCPService(index=index, allow_mutations=False)
    monkeypatch.setattr(cli, "_get_runtime_index", lambda: index)

    groups_cli = runner.invoke(cli.app, ["groups", "--json"])
    resources_cli = runner.invoke(cli.app, ["resources", "dcim", "--json"])
    ops_cli = runner.invoke(cli.app, ["ops", "dcim", "devices", "--json"])
    capabilities_cli = runner.invoke(cli.app, ["capabilities", "--json"])

    assert groups_cli.exit_code == 0
    assert resources_cli.exit_code == 0
    assert ops_cli.exit_code == 0
    assert capabilities_cli.exit_code == 0
    assert json.loads(groups_cli.output) == await service.list_groups()
    assert json.loads(resources_cli.output) == await service.list_resources(group="dcim")
    assert json.loads(ops_cli.output) == await service.describe_operation(
        group="dcim", resource="devices"
    )
    capabilities = json.loads(capabilities_cli.output)
    described = await service.describe_operation(group="dcim", resource="devices")
    assert capabilities["groups"]["dcim"]["devices"] == {
        "operations": described["operations"],
        "filters": described["filters"],
    }


def _run_hook(command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_nbx_write.py")],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=False,
    )


def test_hook_blocks_unconfirmed_delete_and_allows_confirmed_delete() -> None:
    blocked = _run_hook("nbx dcim devices delete --id 7")
    allowed = _run_hook("NETBOX_SDK_CONFIRM_WRITE=1 nbx dcim devices delete --id 7")
    marker_after = _run_hook("nbx dcim devices delete --id 7 NETBOX_SDK_CONFIRM_WRITE=1")

    assert blocked.returncode == 0
    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""
    assert json.loads(marker_after.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_does_not_interfere_with_unrelated_bash() -> None:
    result = _run_hook("git status --short && printf safe")
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_fails_closed_for_malformed_nbx_write() -> None:
    result = _run_hook("nbx dcim devices delete --body-json '{")
    assert result.returncode == 0
    assert json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "post", "Delete"])
def test_hook_blocks_unconfirmed_raw_call_write(method: str) -> None:
    blocked = _run_hook(f"nbx call {method} /api/dcim/devices/1/")
    allowed = _run_hook(f"NETBOX_SDK_CONFIRM_WRITE=1 nbx call {method} /api/dcim/devices/1/")

    assert blocked.returncode == 0
    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""


@pytest.mark.parametrize("method", ["GET", "HEAD", "get"])
def test_hook_allows_unconfirmed_raw_call_read(method: str) -> None:
    result = _run_hook(f"nbx call {method} /api/dcim/devices/1/")
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("root", ["branching", "branch"])
@pytest.mark.parametrize(
    "verb_invocation",
    [
        'create --name "my-branch"',
        "update 7 --name renamed",
        "delete 7 --yes",
        "sync 7",
        "merge 7",
        "revert 7",
        "archive 7 --yes",
    ],
)
def test_hook_blocks_unconfirmed_branching_writes(root: str, verb_invocation: str) -> None:
    """Branching verbs sit right after the group name, not at a fixed slice
    end — this covers every mutating verb including sync/merge/revert/archive,
    which aren't in WRITE_ACTIONS at all, on both the `branching` and `branch`
    alias roots."""
    blocked = _run_hook(f"nbx {root} {verb_invocation}")
    allowed = _run_hook(f"NETBOX_SDK_CONFIRM_WRITE=1 nbx {root} {verb_invocation}")

    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""


@pytest.mark.parametrize(
    "read_invocation",
    [
        "status",
        "list",
        "show 7",
        "events --branch 7",
        "changes --branch 7 --action create",
        "models",
    ],
)
def test_hook_allows_unconfirmed_branching_reads(read_invocation: str) -> None:
    """`changes --action create` exercises the filter value literally named
    after a write action, which must not trip the write gate."""
    result = _run_hook(f"nbx branching {read_invocation}")
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_blocks_unconfirmed_proxbox_sync() -> None:
    blocked = _run_hook("nbx proxbox sync")
    allowed = _run_hook("NETBOX_SDK_CONFIRM_WRITE=1 nbx proxbox sync")
    blocked_endpoint = _run_hook("nbx proxbox sync my-endpoint --type virtual-machines")

    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""
    assert json.loads(blocked_endpoint.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_hook_allows_unconfirmed_proxbox_sync_types() -> None:
    result = _run_hook("nbx proxbox sync-types")
    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize("verb", ["post", "put", "patch", "delete"])
def test_hook_blocks_unconfirmed_dev_http_writes(verb: str) -> None:
    """`post`/`put` are mutating but were never members of WRITE_ACTIONS, so
    they only ever matched the old slice check by accident (via `patch`/
    `delete` sharing literal spelling with unrelated action names)."""
    blocked = _run_hook(f"nbx dev http {verb} --path /api/dcim/devices/1/")
    allowed = _run_hook(
        f"NETBOX_SDK_CONFIRM_WRITE=1 nbx dev http {verb} --path /api/dcim/devices/1/"
    )

    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""


@pytest.mark.parametrize("read_invocation", ["get --path /api/dcim/devices/", "paths", "ops"])
def test_hook_allows_unconfirmed_dev_http_reads(read_invocation: str) -> None:
    result = _run_hook(f"nbx dev http {read_invocation}")
    assert result.returncode == 0
    assert result.stdout == ""


def test_hook_blocks_unconfirmed_nested_plugin_catalog_write() -> None:
    """A write action at the end of a deeper-than-usual resource path (e.g. a
    Proxbox catalog sub-namespace) must still be caught; the detector keys
    off the trailing positional rather than a fixed index."""
    blocked = _run_hook("nbx proxbox endpoints proxmox create --body-json '{}'")
    allowed = _run_hook(
        "NETBOX_SDK_CONFIRM_WRITE=1 nbx proxbox endpoints proxmox create --body-json '{}'"
    )

    assert json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert allowed.returncode == 0
    assert allowed.stdout == ""


def test_is_loopback_host() -> None:
    assert is_loopback_host("127.0.0.1")
    assert is_loopback_host("localhost")
    assert is_loopback_host("::1")
    assert not is_loopback_host("0.0.0.0")
    assert not is_loopback_host("10.0.0.5")


def _trivial_app() -> Starlette:
    async def _handler(request: Any) -> PlainTextResponse:
        return PlainTextResponse("ok")

    return Starlette(routes=[Route("/", _handler)])


@pytest.mark.asyncio
async def test_bearer_token_middleware_enforces_shared_secret() -> None:
    app = BearerTokenMiddleware(_trivial_app(), "secret-token")
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        missing = await client.get("/")
        wrong = await client.get("/", headers={"Authorization": "Bearer nope"})
        wrong_scheme = await client.get("/", headers={"Authorization": "Basic secret-token"})
        correct = await client.get("/", headers={"Authorization": "Bearer secret-token"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert wrong_scheme.status_code == 401
    assert correct.status_code == 200
    assert correct.text == "ok"


def test_build_streamable_http_app_only_wraps_when_token_configured() -> None:
    server = create_mcp_server(host="127.0.0.1", port=8000)

    unwrapped = build_streamable_http_app(server, auth_token=None)
    wrapped = build_streamable_http_app(server, auth_token="secret")

    assert not isinstance(unwrapped, BearerTokenMiddleware)
    assert isinstance(wrapped, BearerTokenMiddleware)


def test_run_streamable_http_fails_closed_without_auth_token(monkeypatch) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV_VAR, raising=False)
    with pytest.raises(RuntimeError, match="loopback"):
        netbox_mcp.run(["--transport", "streamable-http", "--host", "0.0.0.0"])


def test_run_streamable_http_allows_non_loopback_with_configured_token(monkeypatch) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV_VAR, raising=False)
    captured: dict[str, Any] = {}

    async def _fake_run(server: Any, *, host: str, port: int, auth_token: str | None) -> None:
        captured.update(host=host, port=port, auth_token=auth_token)

    monkeypatch.setattr(netbox_mcp, "_run_streamable_http", _fake_run)

    netbox_mcp.run(
        ["--transport", "streamable-http", "--host", "0.0.0.0", "--auth-token", "secret"]
    )

    assert captured == {"host": "0.0.0.0", "port": 8000, "auth_token": "secret"}


def test_run_streamable_http_reads_auth_token_from_env(monkeypatch) -> None:
    monkeypatch.setenv(AUTH_TOKEN_ENV_VAR, "env-secret")
    captured: dict[str, Any] = {}

    async def _fake_run(server: Any, *, host: str, port: int, auth_token: str | None) -> None:
        captured.update(host=host, port=port, auth_token=auth_token)

    monkeypatch.setattr(netbox_mcp, "_run_streamable_http", _fake_run)

    netbox_mcp.run(["--transport", "streamable-http", "--host", "0.0.0.0"])

    assert captured["auth_token"] == "env-secret"


def test_run_streamable_http_fails_closed_on_loopback_without_token(monkeypatch) -> None:
    # Binding to a loopback host only restricts *reachability* to this
    # machine; it does not *authenticate* other local processes or users, so
    # an auth token is required even here.
    monkeypatch.delenv(AUTH_TOKEN_ENV_VAR, raising=False)
    captured: dict[str, Any] = {}

    async def _fake_run(server: Any, *, host: str, port: int, auth_token: str | None) -> None:
        captured.update(host=host, port=port, auth_token=auth_token)

    monkeypatch.setattr(netbox_mcp, "_run_streamable_http", _fake_run)

    with pytest.raises(RuntimeError, match="loopback"):
        netbox_mcp.run(["--transport", "streamable-http"])

    assert captured == {}


def test_run_streamable_http_allows_loopback_with_configured_token(monkeypatch) -> None:
    monkeypatch.delenv(AUTH_TOKEN_ENV_VAR, raising=False)
    captured: dict[str, Any] = {}

    async def _fake_run(server: Any, *, host: str, port: int, auth_token: str | None) -> None:
        captured.update(host=host, port=port, auth_token=auth_token)

    monkeypatch.setattr(netbox_mcp, "_run_streamable_http", _fake_run)

    netbox_mcp.run(["--transport", "streamable-http", "--auth-token", "secret"])

    assert captured == {"host": "127.0.0.1", "port": 8000, "auth_token": "secret"}
