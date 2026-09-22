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
        use_cache: bool = True,
    ) -> ApiResponse:
        del headers, use_cache
        self.calls.append({"method": method, "path": path, "query": query, "payload": payload})
        body = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        return ApiResponse(status=200, text=json.dumps(body), headers={})


_EXPECTED_RPC_COLLECTION_ACTIONS = {
    "settings": ("list", "get", "patch"),
    "backends": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "procedures": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "procedure-commands": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "intents": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "linux-service-allowlist": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "netbox-plugin-allowlist": (
        "list",
        "get",
        "create",
        "update",
        "patch",
        "delete",
        "bulk-update",
        "bulk-patch",
        "bulk-delete",
    ),
    "executions": ("list", "get", "create"),
    "execution-events": ("list", "get"),
}


def _assert_fixed_rpc_collection_oracle(resources: dict[str, tuple[str, ...]]) -> None:
    assert resources == _EXPECTED_RPC_COLLECTION_ACTIONS


def test_official_plugin_registry_is_explicit_and_resolvable() -> None:
    assert [plugin.package for plugin in official_plugins()] == [
        "netbox-rpc",
        "netbox-proxbox",
    ]
    assert official_plugin("rpc") == official_plugin("netbox_rpc")
    assert official_plugin("proxbox") == official_plugin("netbox-proxbox")
    assert official_plugin("third-party") is None


def test_rpc_fixed_collection_matrix_covers_every_router_resource() -> None:
    _assert_fixed_rpc_collection_oracle(
        {spec.key: spec.supported_actions for spec in rpc_resources()}
    )


def test_rpc_fixed_collection_oracle_detects_route_omission() -> None:
    incomplete = dict(_EXPECTED_RPC_COLLECTION_ACTIONS)
    incomplete.pop("netbox-plugin-allowlist")

    with pytest.raises(AssertionError):
        _assert_fixed_rpc_collection_oracle(incomplete)


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


async def test_rpc_read_workflows_forward_queries_without_losing_repeated_values() -> None:
    fake = _FakeClient()
    client = RPCClient(fake)  # type: ignore[arg-type]

    await client.available_procedures(
        target_type="DCIM.Device",
        query={"tag": ["edge", "managed"], "target_type": "ignored"},
    )
    await client.procedure_commands(2, query={"limit": "25", "tag": ["a", "b"]})
    await client.execution_events(5, query={"level": ["warning", "error"]})

    assert fake.calls == [
        {
            "method": "GET",
            "path": "/api/plugins/rpc/procedures/available/",
            "query": {"tag": ["edge", "managed"], "target_type": "dcim.device"},
            "payload": None,
        },
        {
            "method": "GET",
            "path": "/api/plugins/rpc/procedures/2/commands/",
            "query": {"limit": "25", "tag": ["a", "b"]},
            "payload": None,
        },
        {
            "method": "GET",
            "path": "/api/plugins/rpc/executions/5/events/",
            "query": {"level": ["warning", "error"]},
            "payload": None,
        },
    ]


async def test_rpc_procedure_commands_rejects_query_on_post_before_request() -> None:
    fake = _FakeClient()

    with pytest.raises(ValueError, match="only supported when listing"):
        await RPCClient(fake).procedure_commands(  # type: ignore[arg-type]
            2,
            query={"limit": "25"},
            payload={"argv": ["true"]},
        )

    assert fake.calls == []


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
    ("resource", "collection_path"),
    [
        ("backends", "/api/plugins/rpc/backends/"),
        ("procedures", "/api/plugins/rpc/procedures/"),
        ("procedure-commands", "/api/plugins/rpc/procedure-commands/"),
        ("intents", "/api/plugins/rpc/intents/"),
        ("linux-service-allowlist", "/api/plugins/rpc/linux-service-allowlist/"),
        ("netbox-plugin-allowlist", "/api/plugins/rpc/netbox-plugin-allowlist/"),
    ],
)
@pytest.mark.parametrize(
    ("action", "object_id", "payload", "method", "path_suffix"),
    [
        ("list", None, None, "GET", "/"),
        ("get", 7, None, "GET", "/7/"),
        ("create", None, {"name": "single"}, "POST", "/"),
        ("create", None, [{"name": "first"}, {"name": "second"}], "POST", "/"),
        ("update", 7, {"id": 7, "name": "replacement"}, "PUT", "/7/"),
        ("patch", 7, {"name": "partial"}, "PATCH", "/7/"),
        ("delete", 7, None, "DELETE", "/7/"),
        ("bulk-update", None, [{"id": 7}], "PUT", "/"),
        ("bulk-patch", None, [{"id": 7}], "PATCH", "/"),
        ("bulk-delete", None, [{"id": 7}], "DELETE", "/"),
    ],
)
async def test_rpc_mutable_collection_exact_standard_transport(
    resource: str,
    collection_path: str,
    action: str,
    object_id: int | None,
    payload: dict[str, Any] | list[dict[str, Any]] | None,
    method: str,
    path_suffix: str,
) -> None:
    fake = _FakeClient()

    await RPCClient(fake).request(  # type: ignore[arg-type]
        resource,
        action,
        object_id=object_id,
        payload=payload,
    )

    assert fake.calls == [
        {
            "method": method,
            "path": f"{collection_path.rstrip('/')}{path_suffix}",
            "query": {},
            "payload": payload,
        }
    ]


@pytest.mark.parametrize(
    ("resource", "action", "object_id", "payload", "method", "path"),
    [
        ("settings", "list", None, None, "GET", "/api/plugins/rpc/settings/"),
        ("settings", "get", 1, None, "GET", "/api/plugins/rpc/settings/1/"),
        (
            "settings",
            "patch",
            1,
            {"enabled": True},
            "PATCH",
            "/api/plugins/rpc/settings/1/",
        ),
        ("executions", "list", None, None, "GET", "/api/plugins/rpc/executions/"),
        ("executions", "get", 7, None, "GET", "/api/plugins/rpc/executions/7/"),
        (
            "executions",
            "create",
            None,
            {"procedure_id": 2},
            "POST",
            "/api/plugins/rpc/executions/",
        ),
        (
            "execution-events",
            "list",
            None,
            None,
            "GET",
            "/api/plugins/rpc/execution-events/",
        ),
        (
            "execution-events",
            "get",
            9,
            None,
            "GET",
            "/api/plugins/rpc/execution-events/9/",
        ),
    ],
)
async def test_rpc_restricted_collection_exact_standard_transport(
    resource: str,
    action: str,
    object_id: int | None,
    payload: dict[str, Any] | None,
    method: str,
    path: str,
) -> None:
    fake = _FakeClient()

    await RPCClient(fake).request(  # type: ignore[arg-type]
        resource,
        action,
        object_id=object_id,
        payload=payload,
    )

    assert fake.calls == [{"method": method, "path": path, "query": {}, "payload": payload}]


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


async def test_rpc_wait_bypasses_response_cache_on_every_poll(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    responses = [{"status": "running"}, {"status": "succeeded"}]

    class CacheAwareClient:
        async def request(
            self,
            method: str,
            path: str,
            *,
            use_cache: bool = True,
        ) -> ApiResponse:
            calls.append({"method": method, "path": path, "use_cache": use_cache})
            return ApiResponse(status=200, text=json.dumps(responses.pop(0)), headers={})

    async def fake_sleep(_delay: float) -> None:
        return None

    monkeypatch.setattr("netbox_sdk.rpc.asyncio.sleep", fake_sleep)
    response = await RPCClient(CacheAwareClient()).wait_for_execution(9, interval=0.25)  # type: ignore[arg-type]

    assert response.json() == {"status": "succeeded"}
    assert calls == [
        {
            "method": "GET",
            "path": "/api/plugins/rpc/executions/9/",
            "use_cache": False,
        },
        {
            "method": "GET",
            "path": "/api/plugins/rpc/executions/9/",
            "use_cache": False,
        },
    ]


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
