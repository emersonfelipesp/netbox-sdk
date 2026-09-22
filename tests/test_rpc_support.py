"""Contract tests for official plugins and netbox-rpc SDK support."""

from __future__ import annotations

import json
from typing import Any

import pytest

from netbox_sdk.client import ApiResponse
from netbox_sdk.plugins import official_plugin, official_plugins
from netbox_sdk.rpc import RPCClient, build_rpc_schema_index, rpc_resources

pytestmark = pytest.mark.suite_sdk


class _FakeClient:
    def __init__(self, responses: list[dict[str, Any]] | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses = list(responses or [{"ok": True}])

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        self.calls.append({"method": method, "path": path, "query": query, "payload": payload})
        body = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return ApiResponse(status=200, text=json.dumps(body), headers={})


def test_official_plugin_registry_is_explicit_and_resolvable() -> None:
    assert [plugin.package for plugin in official_plugins()] == [
        "netbox-rpc",
        "netbox-proxbox",
    ]
    assert official_plugin("rpc") == official_plugin("netbox_rpc")
    assert official_plugin("proxbox") == official_plugin("netbox-proxbox")
    assert official_plugin("third-party") is None


def test_rpc_fixed_collection_matrix_covers_every_router_resource() -> None:
    resources = {spec.key: spec for spec in rpc_resources()}
    assert set(resources) == {
        "settings",
        "backends",
        "procedures",
        "procedure-commands",
        "intents",
        "linux-service-allowlist",
        "executions",
        "execution-events",
    }
    assert resources["settings"].supported_actions == ("list", "get", "patch")
    assert resources["executions"].supported_actions == ("list", "get", "create")
    assert resources["execution-events"].supported_actions == ("list", "get")
    mutable_actions = (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    )
    for key in (
        "backends",
        "procedures",
        "procedure-commands",
        "intents",
        "linux-service-allowlist",
    ):
        assert resources[key].supported_actions == mutable_actions


def test_rpc_schema_index_contains_fixed_crud_contract() -> None:
    index = build_rpc_schema_index()
    assert set(index.resources("plugins")) == {f"rpc/{spec.key}" for spec in rpc_resources()}
    operations = {
        (item.method, item.path) for item in index.operations_for("plugins", "rpc/executions")
    }
    assert operations == {
        ("GET", "/api/plugins/rpc/executions/"),
        ("POST", "/api/plugins/rpc/executions/"),
        ("GET", "/api/plugins/rpc/executions/{id}/"),
    }


async def test_rpc_client_covers_every_custom_action() -> None:
    fake = _FakeClient()
    client = RPCClient(fake)  # type: ignore[arg-type]
    await client.available_procedures(target_type="DCIM.Device")
    await client.procedure_commands(2)
    await client.procedure_commands(2, payload={"argv": ["true"]})
    await client.run_intent(
        3,
        assigned_object_type="dcim.device",
        assigned_object_id=4,
        params={"service_slug": "nginx"},
    )
    for action in ("cancel", "approve", "reject"):
        await client.execution_action(5, action, reason="reviewed")
    await client.execution_events(5)

    assert [(call["method"], call["path"]) for call in fake.calls] == [
        ("GET", "/api/plugins/rpc/procedures/available/"),
        ("GET", "/api/plugins/rpc/procedures/2/commands/"),
        ("POST", "/api/plugins/rpc/procedures/2/commands/"),
        ("POST", "/api/plugins/rpc/intents/3/run/"),
        ("POST", "/api/plugins/rpc/executions/5/cancel/"),
        ("POST", "/api/plugins/rpc/executions/5/approve/"),
        ("POST", "/api/plugins/rpc/executions/5/reject/"),
        ("GET", "/api/plugins/rpc/executions/5/events/"),
    ]
    assert fake.calls[0]["query"] == {"target_type": "dcim.device"}
    assert fake.calls[3]["payload"]["assigned_object_type"] == "dcim.device"


async def test_rpc_client_covers_standard_crud_with_resource_policy() -> None:
    fake = _FakeClient()
    client = RPCClient(fake)  # type: ignore[arg-type]
    await client.request("backends", "patch", object_id=7, payload={"verify_ssl": True})
    assert fake.calls == [
        {
            "method": "PATCH",
            "path": "/api/plugins/rpc/backends/7/",
            "query": {},
            "payload": {"verify_ssl": True},
        }
    ]
    with pytest.raises(ValueError, match="not supported"):
        await client.request("execution-events", "delete", object_id=1)


@pytest.mark.parametrize(
    ("action", "method"),
    [("bulk-update", "PUT"), ("bulk-patch", "PATCH"), ("bulk-delete", "DELETE")],
)
async def test_rpc_client_bulk_actions_use_collection_and_array_body(
    action: str, method: str
) -> None:
    fake = _FakeClient()
    await RPCClient(fake).request("backends", action, payload=[{"id": 7}])  # type: ignore[arg-type]
    assert fake.calls == [
        {
            "method": method,
            "path": "/api/plugins/rpc/backends/",
            "query": {},
            "payload": [{"id": 7}],
        }
    ]


async def test_rpc_wait_stops_on_expired_without_sleeping() -> None:
    fake = _FakeClient([{"status": "expired"}])
    response = await RPCClient(fake).wait_for_execution(9)  # type: ignore[arg-type]
    assert response.json() == {"status": "expired"}
    assert len(fake.calls) == 1


async def test_rpc_wait_polls_from_nonterminal_to_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeClient([{"status": "running"}, {"status": "succeeded"}])
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("netbox_sdk.rpc.asyncio.sleep", fake_sleep)
    response = await RPCClient(fake).wait_for_execution(9, interval=0.25)  # type: ignore[arg-type]
    assert response.json() == {"status": "succeeded"}
    assert sleeps == [0.25]
    assert len(fake.calls) == 2


async def test_rpc_wait_returns_http_error_response() -> None:
    class ErrorClient(_FakeClient):
        async def request(self, *args: Any, **kwargs: Any) -> ApiResponse:
            await super().request(*args, **kwargs)
            return ApiResponse(status=503, text='{"detail":"unavailable"}', headers={})

    fake = ErrorClient()
    response = await RPCClient(fake).wait_for_execution(9)  # type: ignore[arg-type]
    assert response.status == 503
    assert len(fake.calls) == 1


@pytest.mark.parametrize("payload", [{"status": "running"}, [], "invalid"])
async def test_rpc_wait_times_out_for_nonterminal_or_malformed_success(
    monkeypatch: pytest.MonkeyPatch, payload: Any
) -> None:
    fake = _FakeClient([payload])

    async def fake_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("netbox_sdk.rpc.asyncio.sleep", fake_sleep)
    with pytest.raises(TimeoutError, match="did not finish"):
        await RPCClient(fake).wait_for_execution(9, timeout=0.001, interval=0.001)  # type: ignore[arg-type]
    assert fake.calls


@pytest.mark.parametrize(
    "field,value",
    [("timeout", float("nan")), ("timeout", float("inf")), ("interval", float("inf"))],
)
async def test_rpc_wait_rejects_nonfinite_bounds_before_request(field: str, value: float) -> None:
    fake = _FakeClient()
    kwargs = {field: value}
    with pytest.raises(ValueError, match="must be finite"):
        await RPCClient(fake).wait_for_execution(9, **kwargs)  # type: ignore[arg-type]
    assert fake.calls == []


@pytest.mark.parametrize("field,value", [("timeout", 0.0), ("interval", -1.0)])
async def test_rpc_wait_rejects_nonpositive_bounds_before_request(field: str, value: float) -> None:
    fake = _FakeClient()
    with pytest.raises(ValueError, match="greater than zero"):
        await RPCClient(fake).wait_for_execution(9, **{field: value})  # type: ignore[arg-type]
    assert fake.calls == []


async def test_rpc_client_rejects_unknown_action_before_request() -> None:
    fake = _FakeClient()
    with pytest.raises(ValueError, match="Unsupported RPC execution action"):
        await RPCClient(fake).execution_action(5, "rerun")  # type: ignore[arg-type]
    assert fake.calls == []
