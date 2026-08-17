"""Schema-driven, transport-independent implementation of NetBox MCP tools."""

from __future__ import annotations

import inspect
import json
import os
from collections.abc import Callable
from typing import Any

from netbox_mcp.models import (
    BulkMutationInput,
    CallInput,
    DeleteInput,
    DetailMutationInput,
    GetInput,
    GroupInput,
    ListInput,
    LiveInput,
    LiveResourceInput,
    MutationInput,
    PluginCallToolInput,
    PluginDiscoverInput,
    PluginListToolsInput,
    ResourceInput,
)
from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.config import Config, load_profile_config
from netbox_sdk.exceptions import ResponseSizeLimitError
from netbox_sdk.introspection import (
    serialize_groups,
    serialize_resource_description,
    serialize_resources,
)
from netbox_sdk.plugin_bridge import (
    BRIDGE_SCHEMA_VERSION,
    MAX_INSTANCE_BYTES,
    PluginBridgeError,
    discover_plugin_manifests,
    parse_plugin_tool_response_document,
    plugin_arguments_to_query,
    plugin_tool_request_path,
    validate_plugin_tool_arguments,
    validate_plugin_tool_response,
)
from netbox_sdk.plugin_discovery import enrich_schema_index_with_runtime_resources
from netbox_sdk.schema import SchemaIndex
from netbox_sdk.schema_resolution import (
    bundled_index,
    requested_netbox_version,
    resolve_index,
)
from netbox_sdk.services import (
    ResolvedRequest,
    list_all_pages,
    parse_header_pairs,
    parse_key_value_pairs,
    resolve_dynamic_request,
)

MUTATION_ENV_VAR = "NETBOX_MCP_ALLOW_MUTATIONS"
DRY_RUN_NOTICE = (
    "Local request preview only; this is not server-side validation and does not prove "
    "that the live NetBox write will succeed."
)
_READ_METHODS = frozenset({"GET", "HEAD"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

ClientFactory = Callable[[Config], NetBoxApiClient]
ConfigLoader = Callable[[], Config]
StringList = list[str]
JsonList = list[Any]
ObjectList = list[dict[str, Any]]


def mutations_enabled_from_env() -> bool:
    """Return whether the process environment explicitly enables writes."""
    return os.environ.get(MUTATION_ENV_VAR, "").strip().lower() in _TRUE_VALUES


class MutationDeniedError(PermissionError):
    """Raised when a live write is attempted while the mutation gate is closed."""


class NetBoxMCPService:
    """Implement the narrow MCP grammar over the standalone SDK."""

    def __init__(
        self,
        *,
        index: SchemaIndex | None = None,
        client_factory: ClientFactory = NetBoxApiClient,
        config_loader: ConfigLoader = load_profile_config,
        allow_mutations: bool | None = None,
    ) -> None:
        # Resolve the operator's release-line pin once, at construction. A
        # long-lived server must not re-read process-global argv/env on every
        # tool call, but the pin it was started with has to reach the live index
        # too, so it is captured here and passed explicitly below.
        self._pinned_line = requested_netbox_version()
        self.index = index if index is not None else bundled_index(self._pinned_line)
        self._client_factory = client_factory
        self._config_loader = config_loader
        self.allow_mutations = (
            mutations_enabled_from_env() if allow_mutations is None else allow_mutations
        )

    def _make_client(self, token: str | None) -> NetBoxApiClient:
        config = self._config_loader()
        if token is not None:
            config = config.model_copy(update={"token_key": None, "token_secret": None})
        client = self._client_factory(config)
        if token is not None:
            client.persistent_headers["Authorization"] = f"Bearer {token}"
        return client

    async def _close_client(self, client: NetBoxApiClient) -> None:
        result = client.close()
        if inspect.isawaitable(result):
            await result

    def _headers(self, values: StringList, token: str | None) -> dict[str, str]:
        headers = parse_header_pairs(values)
        if token is not None:
            headers = {
                name: value for name, value in headers.items() if name.casefold() != "authorization"
            }
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _live_index(self, token: str | None) -> SchemaIndex:
        client = self._make_client(token)
        try:
            index = await resolve_index(client, prefer_live=True, line=self._pinned_line)
            await enrich_schema_index_with_runtime_resources(index, client)
            return index
        finally:
            await self._close_client(client)

    async def _selected_index(self, *, live: bool, token: str | None) -> SchemaIndex:
        return await self._live_index(token) if live else self.index

    def _ensure_resource(self, index: SchemaIndex, group: str, resource: str) -> None:
        if index.resource_paths(group, resource) is None:
            raise ValueError(f"Resource not found: {group}/{resource}")

    def _ensure_mutations_allowed(self) -> None:
        if not self.allow_mutations:
            raise MutationDeniedError(
                f"NetBox mutations are disabled. Set {MUTATION_ENV_VAR}=1 or start "
                "nbx-mcp with --allow-mutations to opt in explicitly."
            )

    @staticmethod
    def _response(response: ApiResponse) -> dict[str, Any]:
        try:
            body: Any = json.loads(response.text)
        except json.JSONDecodeError:
            body = response.text
        return {
            "status": response.status,
            "headers": dict(response.headers),
            "body": body,
        }

    @staticmethod
    def _dry_run(resolved: ResolvedRequest) -> dict[str, Any]:
        return {
            "dry_run": True,
            "method": resolved.method,
            "path": resolved.path,
            "query": resolved.query,
            "body": resolved.payload,
            "notice": DRY_RUN_NOTICE,
        }

    async def list_groups(self, *, live: bool = False, token: str | None = None) -> dict[str, Any]:
        values = LiveInput.model_validate({"live": live, "token": token})
        index = await self._selected_index(live=values.live, token=values.token)
        return serialize_groups(index)

    async def list_resources(
        self,
        *,
        group: str,
        live: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = GroupInput.model_validate({"group": group, "live": live, "token": token})
        index = await self._selected_index(live=values.live, token=values.token)
        resources = index.resources(values.group)
        if not resources:
            raise ValueError(f"Group not found or has no resources: {values.group}")
        return serialize_resources(index, values.group)

    async def describe_operation(
        self,
        *,
        group: str,
        resource: str,
        live: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = LiveResourceInput.model_validate(
            {"group": group, "resource": resource, "live": live, "token": token}
        )
        index = await self._selected_index(live=values.live, token=values.token)
        self._ensure_resource(index, values.group, values.resource)
        return serialize_resource_description(index, values.group, values.resource)

    async def list(
        self,
        *,
        group: str,
        resource: str,
        query: StringList | None = None,
        all: bool = False,
        max_records: int = 10_000,
        header: StringList | None = None,
        live: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = ListInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "query": query or [],
                "all": all,
                "max_records": max_records,
                "header": header or [],
                "live": live,
                "token": token,
            }
        )
        index = await self._selected_index(live=values.live, token=values.token)
        self._ensure_resource(index, values.group, values.resource)
        client = self._make_client(values.token)
        headers = self._headers(values.header, values.token)
        header_pairs = [f"{name}: {value}" for name, value in headers.items()]
        try:
            if values.all:
                response = await list_all_pages(
                    client,
                    index,
                    values.group,
                    values.resource,
                    query_pairs=values.query,
                    header_pairs=header_pairs,
                    max_records=values.max_records,
                )
            else:
                resolved = resolve_dynamic_request(
                    index,
                    values.group,
                    values.resource,
                    "list",
                    object_id=None,
                    query=parse_key_value_pairs(values.query),
                    payload=None,
                )
                response = await client.request(
                    resolved.method,
                    resolved.path,
                    query=resolved.query,
                    payload=None,
                    headers=self._headers(values.header, values.token) or None,
                )
            return self._response(response)
        finally:
            await self._close_client(client)

    async def get(
        self,
        *,
        group: str,
        resource: str,
        id: int,
        header: StringList | None = None,
        live: bool = False,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = GetInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "id": id,
                "header": header or [],
                "live": live,
                "token": token,
            }
        )
        index = await self._selected_index(live=values.live, token=values.token)
        resolved = resolve_dynamic_request(
            index,
            values.group,
            values.resource,
            "get",
            object_id=values.id,
            query={},
            payload=None,
        )
        client = self._make_client(values.token)
        try:
            response = await client.request(
                resolved.method,
                resolved.path,
                query={},
                payload=None,
                headers=self._headers(values.header, values.token) or None,
            )
            return self._response(response)
        finally:
            await self._close_client(client)

    def filters(self, *, group: str, resource: str) -> dict[str, Any]:
        values = ResourceInput.model_validate({"group": group, "resource": resource})
        self._ensure_resource(self.index, values.group, values.resource)
        description = serialize_resource_description(self.index, values.group, values.resource)
        return {
            "group": values.group,
            "resource": values.resource,
            "filters": description["filters"],
        }

    async def _mutate(
        self,
        *,
        action: str,
        group: str,
        resource: str,
        object_id: int | None,
        payload: dict[str, Any] | JsonList | None,
        dry_run: bool,
        header: StringList,
        token: str | None,
    ) -> dict[str, Any]:
        resolved = resolve_dynamic_request(
            self.index,
            group,
            resource,
            action,
            object_id=object_id,
            query={},
            payload=payload,
        )
        if dry_run:
            return self._dry_run(resolved)
        self._ensure_mutations_allowed()
        client = self._make_client(token)
        try:
            response = await client.request(
                resolved.method,
                resolved.path,
                query={},
                payload=resolved.payload,
                headers=self._headers(header, token) or None,
            )
            return self._response(response)
        finally:
            await self._close_client(client)

    async def create(
        self,
        *,
        group: str,
        resource: str,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = MutationInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "payload": payload,
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        return await self._mutate(
            action="create",
            group=values.group,
            resource=values.resource,
            object_id=None,
            payload=values.payload,
            dry_run=values.dry_run,
            header=values.header,
            token=values.token,
        )

    async def update(
        self,
        *,
        group: str,
        resource: str,
        id: int,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = DetailMutationInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "id": id,
                "payload": payload,
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        return await self._mutate(
            action="update",
            group=values.group,
            resource=values.resource,
            object_id=values.id,
            payload=values.payload,
            dry_run=values.dry_run,
            header=values.header,
            token=values.token,
        )

    async def patch(
        self,
        *,
        group: str,
        resource: str,
        id: int,
        payload: dict[str, Any],
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = DetailMutationInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "id": id,
                "payload": payload,
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        return await self._mutate(
            action="patch",
            group=values.group,
            resource=values.resource,
            object_id=values.id,
            payload=values.payload,
            dry_run=values.dry_run,
            header=values.header,
            token=values.token,
        )

    async def delete(
        self,
        *,
        group: str,
        resource: str,
        id: int,
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = DeleteInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "id": id,
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        return await self._mutate(
            action="delete",
            group=values.group,
            resource=values.resource,
            object_id=values.id,
            payload=None,
            dry_run=values.dry_run,
            header=values.header,
            token=values.token,
        )

    async def _bulk(
        self,
        *,
        action: str,
        group: str,
        resource: str,
        payload: ObjectList,
        dry_run: bool,
        header: StringList | None,
        token: str | None,
    ) -> dict[str, Any]:
        values = BulkMutationInput.model_validate(
            {
                "group": group,
                "resource": resource,
                "payload": payload,
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        return await self._mutate(
            action=action,
            group=values.group,
            resource=values.resource,
            object_id=None,
            payload=values.payload,
            dry_run=values.dry_run,
            header=values.header,
            token=values.token,
        )

    async def bulk_update(
        self,
        *,
        group: str,
        resource: str,
        payload: ObjectList,
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        return await self._bulk(
            action="bulk-update",
            group=group,
            resource=resource,
            payload=payload,
            dry_run=dry_run,
            header=header,
            token=token,
        )

    async def bulk_patch(
        self,
        *,
        group: str,
        resource: str,
        payload: ObjectList,
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        return await self._bulk(
            action="bulk-patch",
            group=group,
            resource=resource,
            payload=payload,
            dry_run=dry_run,
            header=header,
            token=token,
        )

    async def bulk_delete(
        self,
        *,
        group: str,
        resource: str,
        payload: ObjectList,
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        return await self._bulk(
            action="bulk-delete",
            group=group,
            resource=resource,
            payload=payload,
            dry_run=dry_run,
            header=header,
            token=token,
        )

    async def plugin_discover(self, *, plugin: str, token: str | None = None) -> dict[str, Any]:
        values = PluginDiscoverInput.model_validate({"plugin": plugin, "token": token})
        client = self._make_client(values.token)
        try:
            changed = await enrich_schema_index_with_runtime_resources(self.index, client)
        finally:
            await self._close_client(client)
        prefix = f"{values.plugin}/"
        resources = [
            resource for resource in self.index.resources("plugins") if resource.startswith(prefix)
        ]
        return {
            "plugin": values.plugin,
            "changed": changed,
            "group": "plugins",
            "resources": resources,
        }

    async def plugin_list_tools(
        self,
        *,
        plugin: str | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """List validated semantic tools advertised by installed NetBox plugins."""
        values = PluginListToolsInput.model_validate({"plugin": plugin, "token": token})
        client = self._make_client(values.token)
        try:
            catalog = await discover_plugin_manifests(client, plugin=values.plugin)
        finally:
            await self._close_client(client)

        tools: list[dict[str, Any]] = []
        for manifest in catalog.manifests:
            for descriptor in manifest.tools:
                record = descriptor.model_dump(by_alias=True)
                record.update(
                    {
                        "plugin": manifest.plugin,
                        "qualified_name": f"{manifest.plugin}.{descriptor.name}",
                        "request_path": plugin_tool_request_path(manifest.plugin, descriptor),
                    }
                )
                tools.append(record)
        tools.sort(key=lambda item: str(item["qualified_name"]))
        return {
            "schema_version": BRIDGE_SCHEMA_VERSION,
            "tools": tools,
            "problems": [
                {"plugin": problem.plugin, "error": problem.error} for problem in catalog.problems
            ],
        }

    async def plugin_call_tool(
        self,
        *,
        plugin: str,
        tool: str,
        arguments: dict[str, Any] | None = None,
        dry_run: bool = False,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """Validate and invoke one advertised semantic plugin operation."""
        values = PluginCallToolInput.model_validate(
            {
                "plugin": plugin,
                "tool": tool,
                "arguments": arguments or {},
                "dry_run": dry_run,
                "header": header or [],
                "token": token,
            }
        )
        client = self._make_client(values.token)
        try:
            catalog = await discover_plugin_manifests(client, plugin=values.plugin)
            descriptor = catalog.find_tool(values.plugin, values.tool)
            validate_plugin_tool_arguments(descriptor, values.arguments)
            path = plugin_tool_request_path(values.plugin, descriptor)
            is_read = descriptor.effect == "read"
            query = plugin_arguments_to_query(values.arguments) if is_read else {}
            payload = None if is_read else values.arguments

            if values.dry_run:
                return {
                    "dry_run": True,
                    "plugin": values.plugin,
                    "tool": values.tool,
                    "effect": descriptor.effect,
                    "method": descriptor.method,
                    "path": path,
                    "query": query,
                    "body": payload,
                    "notice": DRY_RUN_NOTICE,
                }
            if not is_read:
                self._ensure_mutations_allowed()
            request_headers = self._headers(values.header, values.token) or None

            try:
                response = await client.request_bounded(
                    descriptor.method,
                    path,
                    max_response_bytes=MAX_INSTANCE_BYTES,
                    query=query,
                    payload=payload,
                    headers=request_headers,
                )
            except ResponseSizeLimitError as exc:
                detail = f"response exceeds the {MAX_INSTANCE_BYTES}-byte size limit"
                if not is_read:
                    raise PluginBridgeError(
                        f"plugin write outcome unknown; do not retry blindly ({detail})"
                    ) from exc
                raise PluginBridgeError(f"plugin tool {detail}") from exc
            except Exception as exc:
                if not is_read:
                    raise PluginBridgeError(
                        "plugin write outcome unknown; do not retry blindly "
                        f"(request failed: {type(exc).__name__})"
                    ) from exc
                raise PluginBridgeError(
                    f"plugin tool request failed: {type(exc).__name__}"
                ) from exc

            try:
                if 300 <= response.status < 400:
                    raise PluginBridgeError(
                        f"plugin tool redirects are not allowed (HTTP {response.status})"
                    )
                if not is_read and not 200 <= response.status < 300:
                    raise PluginBridgeError(
                        f"plugin tool returned HTTP {response.status} after dispatch"
                    )
                bodyless = descriptor.method == "HEAD" or response.status in {204, 205}
                body = None if bodyless else parse_plugin_tool_response_document(response.text)
                result = {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "body": body,
                }
                if 200 <= response.status < 300 and not bodyless:
                    validate_plugin_tool_response(descriptor, body)
            except PluginBridgeError as exc:
                if not is_read:
                    raise PluginBridgeError(
                        f"plugin write outcome unknown; do not retry blindly ({exc})"
                    ) from exc
                raise
            return {
                "plugin": values.plugin,
                "tool": values.tool,
                "effect": descriptor.effect,
                **result,
            }
        finally:
            await self._close_client(client)

    async def call(
        self,
        *,
        method: str,
        path: str,
        query: StringList | None = None,
        payload: dict[str, Any] | JsonList | None = None,
        header: StringList | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        values = CallInput.model_validate(
            {
                "method": method,
                "path": path,
                "query": query or [],
                "payload": payload,
                "header": header or [],
                "token": token,
            }
        )
        if values.method not in _READ_METHODS:
            self._ensure_mutations_allowed()
        client = self._make_client(values.token)
        try:
            response = await client.request(
                values.method,
                values.path,
                query=parse_key_value_pairs(values.query),
                payload=values.payload,
                headers=self._headers(values.header, values.token) or None,
            )
            return self._response(response)
        finally:
            await self._close_client(client)
