"""First-class client contract for the netbox-rpc plugin."""

from __future__ import annotations

import asyncio
import math
import time
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.http_cache import QueryParams
from netbox_sdk.schema import SchemaIndex, parse_group_resource
from netbox_sdk.services import resolve_dynamic_request

RPC_BASE = "/api/plugins/rpc"
RPC_TERMINAL_STATUSES = frozenset({"succeeded", "failed", "cancelled", "rejected", "expired"})


class RPCResourceSpec(BaseModel):
    """One collection in the maintained netbox-rpc API contract."""

    model_config = ConfigDict(frozen=True)

    key: str
    command: str
    list_methods: tuple[str, ...]
    detail_methods: tuple[str, ...]

    @property
    def list_path(self) -> str:
        return f"{RPC_BASE}/{self.key}/"

    @property
    def detail_path(self) -> str:
        return f"{self.list_path}{{id}}/"

    @property
    def resource(self) -> str:
        group, resource = parse_group_resource(self.list_path)
        if group != "plugins" or resource is None:
            raise ValueError(f"Invalid RPC plugin list path: {self.list_path}")
        return resource

    @property
    def supported_actions(self) -> tuple[str, ...]:
        actions: list[str] = []
        list_methods = set(self.list_methods)
        detail_methods = set(self.detail_methods)
        if "GET" in list_methods:
            actions.append("list")
        if "GET" in detail_methods:
            actions.append("get")
        if "POST" in list_methods:
            actions.append("create")
        if "PUT" in detail_methods:
            actions.append("update")
        if "PATCH" in detail_methods:
            actions.append("patch")
        if "DELETE" in detail_methods:
            actions.append("delete")
        if "PUT" in list_methods:
            actions.append("bulk-update")
        if "PATCH" in list_methods:
            actions.append("bulk-patch")
        if "DELETE" in list_methods:
            actions.append("bulk-delete")
        return tuple(actions)


def _resource(
    key: str,
    *,
    command: str | None = None,
    list_methods: tuple[str, ...] = ("GET", "POST", "PUT", "PATCH", "DELETE"),
    detail_methods: tuple[str, ...] = ("GET", "PUT", "PATCH", "DELETE"),
) -> RPCResourceSpec:
    return RPCResourceSpec(
        key=key,
        command=command or key,
        list_methods=list_methods,
        detail_methods=detail_methods,
    )


RPC_RESOURCES: tuple[RPCResourceSpec, ...] = (
    _resource("settings", list_methods=("GET",), detail_methods=("GET", "PATCH")),
    _resource("backends"),
    _resource("procedures"),
    _resource("procedure-commands"),
    _resource("intents"),
    _resource("linux-service-allowlist"),
    _resource("netbox-plugin-allowlist"),
    _resource(
        "executions",
        list_methods=("GET", "POST"),
        detail_methods=("GET",),
    ),
    _resource(
        "execution-events",
        list_methods=("GET",),
        detail_methods=("GET",),
    ),
)


def rpc_resources() -> tuple[RPCResourceSpec, ...]:
    return RPC_RESOURCES


def find_rpc_resource(identifier: str) -> RPCResourceSpec:
    """Resolve a maintained RPC collection by command, key, or API resource."""
    normalized = identifier.strip().strip("/")
    for spec in RPC_RESOURCES:
        if normalized in {
            spec.key,
            spec.command,
            spec.resource,
            spec.list_path.strip("/"),
            spec.detail_path.strip("/"),
        }:
            return spec
    available = ", ".join(spec.command for spec in RPC_RESOURCES)
    raise KeyError(f"Unknown RPC resource {identifier!r}. Available: {available}")


def register_rpc_resources(index: SchemaIndex) -> SchemaIndex:
    """Install the maintained RPC collections into a schema index."""
    for spec in RPC_RESOURCES:
        index.add_discovered_resource(
            group="plugins",
            resource=spec.resource,
            list_path=spec.list_path,
            detail_path=spec.detail_path,
            list_methods=spec.list_methods,
            detail_methods=spec.detail_methods,
        )
    return index


def build_rpc_schema_index() -> SchemaIndex:
    """Return a fresh schema index containing the maintained RPC contract."""
    index = SchemaIndex({"openapi": "3.0.0", "paths": {}})
    return register_rpc_resources(index)


class RPCClient:
    """Workflow-aware netbox-rpc client built on ``NetBoxApiClient``."""

    def __init__(self, client: NetBoxApiClient, *, index: SchemaIndex | None = None) -> None:
        self.client = client
        self.index = index or build_rpc_schema_index()

    async def request(
        self,
        resource: str,
        action: str,
        *,
        object_id: int | None = None,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        """Call any maintained standard RPC collection action."""
        spec = find_rpc_resource(resource)
        action_name = action.casefold()
        if action_name not in spec.supported_actions:
            available = ", ".join(spec.supported_actions)
            raise ValueError(
                f"Action {action!r} is not supported for RPC resource "
                f"{spec.command!r}. Available: {available}"
            )
        resolved = resolve_dynamic_request(
            self.index,
            "plugins",
            spec.resource,
            action_name,
            object_id=object_id,
            query=query or {},
            payload=payload,
        )
        kwargs: dict[str, Any] = {
            "query": resolved.query,
            "payload": resolved.payload,
        }
        if headers:
            kwargs["headers"] = headers
        return await self.client.request(resolved.method, resolved.path, **kwargs)

    async def available_procedures(
        self,
        *,
        target_type: str | None = None,
        query: QueryParams | None = None,
    ) -> ApiResponse:
        request_query = dict(query or {})
        if target_type:
            request_query["target_type"] = target_type.strip().lower()
        return await self.client.request(
            "GET",
            f"{RPC_BASE}/procedures/available/",
            query=request_query or None,
        )

    async def procedure_commands(
        self,
        procedure_id: int,
        *,
        query: QueryParams | None = None,
        payload: dict[str, Any] | None = None,
    ) -> ApiResponse:
        if payload is not None and query:
            raise ValueError("query parameters are only supported when listing procedure commands")
        method = "POST" if payload is not None else "GET"
        return await self.client.request(
            method,
            f"{RPC_BASE}/procedures/{procedure_id}/commands/",
            query=query,
            payload=payload,
        )

    async def run_intent(
        self,
        intent_id: int,
        *,
        assigned_object_type: str,
        assigned_object_id: int,
        params: dict[str, Any] | None = None,
    ) -> ApiResponse:
        return await self.client.request(
            "POST",
            f"{RPC_BASE}/intents/{intent_id}/run/",
            payload={
                "assigned_object_type": assigned_object_type,
                "assigned_object_id": assigned_object_id,
                "params": params or {},
            },
        )

    async def execution_action(
        self, execution_id: int, action: str, *, reason: str | None = None
    ) -> ApiResponse:
        if action not in {"cancel", "approve", "reject"}:
            raise ValueError(f"Unsupported RPC execution action: {action}")
        body = {"reason": reason} if action in {"approve", "reject"} and reason else {}
        return await self.client.request(
            "POST", f"{RPC_BASE}/executions/{execution_id}/{action}/", payload=body
        )

    async def execution_events(
        self,
        execution_id: int,
        *,
        query: QueryParams | None = None,
    ) -> ApiResponse:
        return await self.client.request(
            "GET",
            f"{RPC_BASE}/executions/{execution_id}/events/",
            query=query,
        )

    async def wait_for_execution(
        self,
        execution_id: int,
        *,
        timeout: float = 300.0,
        interval: float = 2.0,
        terminal_statuses: Iterable[str] = RPC_TERMINAL_STATUSES,
    ) -> ApiResponse:
        if not math.isfinite(timeout) or not math.isfinite(interval):
            raise ValueError("timeout and interval must be finite")
        if timeout <= 0 or interval <= 0:
            raise ValueError("timeout and interval must be greater than zero")
        terminal = {value.casefold() for value in terminal_statuses}
        deadline = time.monotonic() + timeout
        while True:
            response = await self.client.request(
                "GET",
                f"{RPC_BASE}/executions/{execution_id}/",
                use_cache=False,
            )
            if response.status >= 400:
                return response
            payload = response.json()
            status = str(payload.get("status", "")).casefold() if isinstance(payload, dict) else ""
            if status in terminal:
                return response
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"RPC execution {execution_id} did not finish within {timeout:g}s"
                )
            await asyncio.sleep(min(interval, remaining))


__all__ = [
    "RPC_BASE",
    "RPC_RESOURCES",
    "RPC_TERMINAL_STATUSES",
    "RPCClient",
    "RPCResourceSpec",
    "build_rpc_schema_index",
    "find_rpc_resource",
    "register_rpc_resources",
    "rpc_resources",
]
