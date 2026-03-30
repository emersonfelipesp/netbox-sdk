"""Runtime discovery helpers for NetBox plugin API endpoints.

These helpers walk ``/api/plugins/`` on the connected NetBox instance and
identify plugin collection endpoints that expose REST resources. The TUI uses
the discovered list/detail paths to augment the bundled OpenAPI schema so
plugin resources appear in navigation even when they are not part of the
reference schema shipped with the CLI.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlsplit

from netbox_sdk.client import NetBoxApiClient

logger = logging.getLogger(__name__)

PLUGIN_ROOT = "/api/plugins/"

try:
    import aiohttp
except ModuleNotFoundError:  # pragma: no cover - optional until client runs
    aiohttp = None  # type: ignore[assignment, misc]

_REQUEST_FAILURE_TYPES: tuple[type[BaseException], ...]
if aiohttp is not None:
    _REQUEST_FAILURE_TYPES = (RuntimeError, OSError, aiohttp.ClientError)
else:
    _REQUEST_FAILURE_TYPES = (RuntimeError, OSError)


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


def _plugin_detail_path(list_path: str) -> str | None:
    """Derive a detail URL template ``...{{id}}/`` from a four-segment plugin list path."""
    parts = [part for part in list_path.split("/") if part]
    if len(parts) != 4 or parts[0] != "api" or parts[1] != "plugins":
        return None
    return f"{list_path}{{id}}/"


async def discover_plugin_resource_paths(client: NetBoxApiClient) -> list[tuple[str, str | None]]:
    """Discover plugin collection/detail paths by walking the live plugin API root.

    Failures on individual paths (network errors, non-JSON bodies) are logged at DEBUG
    and skipped so discovery can continue.

    Returns:
        Sorted list of ``(list_path, detail_path_or_none)`` tuples.
    """
    queue: list[str] = [PLUGIN_ROOT]
    visited: set[str] = set()
    discovered: set[tuple[str, str | None]] = set()

    while queue:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)

        try:
            response = await client.request("GET", path)
        except _REQUEST_FAILURE_TYPES as exc:
            logger.debug(
                "plugin discovery request failed for %s: %s",
                path,
                exc,
                extra={"nbx_event": "plugin_discovery_request_error", "request_path": path},
            )
            continue
        except Exception as exc:
            # Tests may use strict mocks that raise outside the aiohttp/OS/runtime bucket.
            logger.debug(
                "plugin discovery request aborted for %s: %s",
                path,
                exc,
                extra={"nbx_event": "plugin_discovery_request_other", "request_path": path},
                exc_info=True,
            )
            continue
        if response.status >= 400:
            logger.debug(
                "plugin discovery skipped path with HTTP %s",
                response.status,
                extra={
                    "nbx_event": "plugin_discovery_http_error",
                    "request_path": path,
                    "http_status": response.status,
                },
            )
            continue
        try:
            payload: Any = response.json()
        except json.JSONDecodeError as exc:
            logger.debug(
                "plugin discovery non-json response for %s: %s",
                path,
                exc,
                extra={"nbx_event": "plugin_discovery_json_error", "request_path": path},
            )
            continue

        if path != PLUGIN_ROOT and _is_collection_payload(payload):
            discovered.add((path, _plugin_detail_path(path)))
            continue

        child_paths = sorted(
            child
            for child in _extract_child_api_paths(payload)
            if child.startswith(PLUGIN_ROOT) and child not in visited
        )
        queue.extend(child_paths)

    return sorted(discovered)
