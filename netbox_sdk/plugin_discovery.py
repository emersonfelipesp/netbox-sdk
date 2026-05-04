"""Runtime discovery helpers for NetBox REST resources outside the bundled schema.

These helpers discover plugin endpoints under ``/api/plugins/`` and NetBox
ObjectType-backed resources exposed by the connected instance. The discovered
paths can augment a mutable :class:`netbox_sdk.schema.SchemaIndex` so Python SDK,
CLI, and TUI callers can reach REST resources that are not part of the bundled
reference schema.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.schema import SchemaIndex, parse_group_resource

logger = logging.getLogger(__name__)

PLUGIN_ROOT = "/api/plugins/"
OBJECT_TYPES_PATH = "/api/core/object-types/"
DISCOVERY_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

try:
    import aiohttp
except ModuleNotFoundError:  # pragma: no cover - optional until client runs
    aiohttp = None  # type: ignore[assignment, misc]

_REQUEST_FAILURE_TYPES: tuple[type[BaseException], ...]
if aiohttp is not None:
    _REQUEST_FAILURE_TYPES = (RuntimeError, OSError, aiohttp.ClientError)
else:
    _REQUEST_FAILURE_TYPES = (RuntimeError, OSError)


@dataclass(frozen=True)
class DiscoveredResource:
    """A REST collection/detail pair discovered from a live NetBox instance."""

    list_path: str
    detail_path: str | None = None
    list_methods: tuple[str, ...] = ("GET",)
    detail_methods: tuple[str, ...] = ("GET",)


def _normalize_api_path(value: str) -> str | None:
    """Return a normalized ``/api/.../`` path or None if ``value`` is not an API path."""
    raw = str(value or "").strip()
    if not raw:
        return None
    if raw.startswith("/api/"):
        path = raw
    else:
        parsed = urlsplit(raw)
        path = parsed.path
    if not path.startswith("/api/"):
        return None
    return path if path.endswith("/") else f"{path}/"


def _extract_child_api_paths(payload: object) -> set[str]:
    """Collect string values under ``payload`` that look like NetBox API paths."""
    discovered: set[str] = set()

    def _walk(value: object) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                _walk(nested)
            return
        if isinstance(value, list):
            for nested in value:
                _walk(nested)
            return
        if isinstance(value, str):
            normalized = _normalize_api_path(value)
            if normalized is not None:
                discovered.add(normalized)

    _walk(payload)
    return discovered


def _is_collection_payload(payload: object) -> bool:
    """True if ``payload`` looks like a paginated NetBox list (``results`` / ``count``)."""
    return isinstance(payload, dict) and ("results" in payload or "count" in payload)


def _detail_path(list_path: str) -> str | None:
    """Derive a detail URL template ``...{{id}}/`` from a normalized list path."""
    parts = [part for part in list_path.split("/") if part]
    if len(parts) < 3 or parts[0] != "api" or "{id}" in parts:
        return None
    return f"{list_path}{{id}}/"


def _plugin_detail_path(list_path: str) -> str | None:
    """Derive a detail URL template for a plugin list path."""
    parts = [part for part in list_path.split("/") if part]
    if len(parts) < 4 or parts[0] != "api" or parts[1] != "plugins":
        return None
    return _detail_path(list_path)


async def _request_json(
    client: NetBoxApiClient,
    method: str,
    path: str,
    *,
    query: dict[str, str] | None = None,
) -> tuple[object, dict[str, str]] | None:
    try:
        if query is None:
            response = await client.request(method, path)
        else:
            response = await client.request(method, path, query=query)
    except _REQUEST_FAILURE_TYPES as exc:
        logger.debug(
            "resource discovery request failed for %s: %s",
            path,
            exc,
            extra={"nbx_event": "resource_discovery_request_error", "request_path": path},
        )
        return None
    except Exception as exc:
        logger.debug(
            "resource discovery request aborted for %s: %s",
            path,
            exc,
            extra={"nbx_event": "resource_discovery_request_other", "request_path": path},
            exc_info=True,
        )
        return None
    if response.status >= 400:
        logger.debug(
            "resource discovery skipped path with HTTP %s",
            response.status,
            extra={
                "nbx_event": "resource_discovery_http_error",
                "request_path": path,
                "http_status": response.status,
            },
        )
        return None
    try:
        return response.json(), response.headers
    except json.JSONDecodeError as exc:
        logger.debug(
            "resource discovery non-json response for %s: %s",
            path,
            exc,
            extra={"nbx_event": "resource_discovery_json_error", "request_path": path},
        )
        return None


def _methods_from_options(payload: object, headers: dict[str, str]) -> set[str]:
    methods: set[str] = set()
    allow = headers.get("Allow") or headers.get("allow") or ""
    for raw_method in allow.split(","):
        method = raw_method.strip().upper()
        if method in DISCOVERY_METHODS:
            methods.add(method)
    if isinstance(payload, dict):
        actions = payload.get("actions")
        if isinstance(actions, dict):
            for raw_method in actions:
                method = str(raw_method).upper()
                if method in DISCOVERY_METHODS:
                    methods.add(method)
    return methods


async def _discover_list_methods(client: NetBoxApiClient, list_path: str) -> tuple[str, ...]:
    discovered = await _request_json(client, "OPTIONS", list_path)
    methods = {"GET"}
    if discovered is not None:
        payload, headers = discovered
        methods.update(_methods_from_options(payload, headers))
    methods.difference_update({"PUT", "PATCH", "DELETE"})
    return tuple(sorted(methods))


def _merge_discovered_resources(resources: list[DiscoveredResource]) -> list[DiscoveredResource]:
    merged: dict[tuple[str, str | None], tuple[set[str], set[str]]] = {}
    for resource in resources:
        key = (resource.list_path, resource.detail_path)
        list_methods, detail_methods = merged.setdefault(key, (set(), set()))
        list_methods.update(method.upper() for method in resource.list_methods)
        detail_methods.update(method.upper() for method in resource.detail_methods)
    return sorted(
        (
            DiscoveredResource(
                list_path=list_path,
                detail_path=detail_path,
                list_methods=tuple(sorted(list_methods or {"GET"})),
                detail_methods=tuple(sorted(detail_methods or {"GET"})),
            )
            for (list_path, detail_path), (list_methods, detail_methods) in merged.items()
        ),
        key=lambda item: (item.list_path, item.detail_path or ""),
    )


async def discover_plugin_resources(client: NetBoxApiClient) -> list[DiscoveredResource]:
    """Discover plugin collection/detail paths by walking the live plugin API root."""
    queue: list[str] = [PLUGIN_ROOT]
    visited: set[str] = set()
    discovered: list[DiscoveredResource] = []

    while queue:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)

        response_data = await _request_json(client, "GET", path)
        if response_data is None:
            continue
        payload, _headers = response_data

        if path != PLUGIN_ROOT and _is_collection_payload(payload):
            discovered.append(
                DiscoveredResource(
                    list_path=path,
                    detail_path=_plugin_detail_path(path),
                    list_methods=await _discover_list_methods(client, path),
                )
            )
            continue

        child_paths = sorted(
            child
            for child in _extract_child_api_paths(payload)
            if child.startswith(PLUGIN_ROOT) and child not in visited
        )
        queue.extend(child_paths)

    return _merge_discovered_resources(discovered)


async def discover_object_type_resources(client: NetBoxApiClient) -> list[DiscoveredResource]:
    """Discover REST resources advertised by NetBox ``core/object-types``."""
    queue: list[tuple[str, dict[str, str] | None]] = [(OBJECT_TYPES_PATH, None)]
    discovered: list[DiscoveredResource] = []

    while queue:
        path, query = queue.pop(0)
        response_data = await _request_json(client, "GET", path, query=query)
        if response_data is None:
            return _merge_discovered_resources(discovered)
        payload, _headers = response_data
        if not isinstance(payload, dict):
            return _merge_discovered_resources(discovered)

        results = payload.get("results")
        if not isinstance(results, list):
            return _merge_discovered_resources(discovered)
        for item in results:
            if not isinstance(item, dict):
                continue
            if item.get("public") is False:
                continue
            list_path = _normalize_api_path(str(item.get("rest_api_endpoint") or ""))
            if list_path is None:
                continue
            group, resource = parse_group_resource(list_path)
            if group is None or resource is None:
                continue
            discovered.append(
                DiscoveredResource(
                    list_path=list_path,
                    detail_path=_detail_path(list_path),
                    list_methods=await _discover_list_methods(client, list_path),
                )
            )

        next_value = payload.get("next")
        if isinstance(next_value, str) and next_value:
            split = urlsplit(next_value)
            next_path = _normalize_api_path(split.path)
            if next_path:
                queue.append((next_path, {key: value for key, value in parse_qsl(split.query)}))

    return _merge_discovered_resources(discovered)


async def discover_runtime_resources(client: NetBoxApiClient) -> list[DiscoveredResource]:
    """Discover plugin and ObjectType-backed resources from a live NetBox instance."""
    plugin_resources = await discover_plugin_resources(client)
    object_type_resources = await discover_object_type_resources(client)
    return _merge_discovered_resources([*plugin_resources, *object_type_resources])


async def enrich_schema_index_with_runtime_resources(
    index: SchemaIndex,
    client: NetBoxApiClient,
) -> bool:
    """Add runtime-discovered resources to ``index`` and return whether it changed."""
    changed = False
    for resource_info in await discover_runtime_resources(client):
        group, resource = parse_group_resource(resource_info.list_path)
        if group is None or resource is None:
            continue
        changed = (
            index.add_discovered_resource(
                group=group,
                resource=resource,
                list_path=resource_info.list_path,
                detail_path=resource_info.detail_path,
                list_methods=resource_info.list_methods,
                detail_methods=resource_info.detail_methods,
            )
            or changed
        )
    return changed


async def discover_plugin_resource_paths(client: NetBoxApiClient) -> list[tuple[str, str | None]]:
    """Backward-compatible plugin path discovery API."""
    return [
        (resource.list_path, resource.detail_path)
        for resource in await discover_plugin_resources(client)
    ]
