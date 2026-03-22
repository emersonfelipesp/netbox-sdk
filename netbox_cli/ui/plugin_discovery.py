"""Runtime discovery helpers for NetBox plugin API endpoints.

These helpers walk ``/api/plugins/`` on the connected NetBox instance and
identify plugin collection endpoints that expose REST resources. The TUI uses
the discovered list/detail paths to augment the bundled OpenAPI schema so
plugin resources appear in navigation even when they are not part of the
reference schema shipped with the CLI.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from netbox_cli.api import NetBoxApiClient

PLUGIN_ROOT = "/api/plugins/"


def _normalize_api_path(value: str) -> str | None:
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
    return isinstance(payload, dict) and ("results" in payload or "count" in payload)


def _plugin_detail_path(list_path: str) -> str | None:
    parts = [part for part in list_path.split("/") if part]
    if len(parts) != 4 or parts[0] != "api" or parts[1] != "plugins":
        return None
    return f"{list_path}{{id}}/"


async def discover_plugin_resource_paths(client: NetBoxApiClient) -> list[tuple[str, str | None]]:
    """Discover plugin collection/detail paths by walking the live plugin API root."""
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
        except Exception:  # noqa: BLE001
            continue
        if response.status >= 400:
            continue
        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
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
