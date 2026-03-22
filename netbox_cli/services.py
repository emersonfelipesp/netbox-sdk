"""Service-layer helpers for resolving dynamic CLI requests from user input."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from .api import ApiResponse, NetBoxApiClient
from .schema import SchemaIndex

ACTION_METHOD_MAP = {
    "list": "GET",
    "get": "GET",
    "create": "POST",
    "update": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}


class ResolvedRequest(BaseModel):
    method: str
    path: str
    query: dict[str, str]
    payload: dict[str, Any] | list[Any] | None


def parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Expected key=value format, got: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Expected key=value format, got: {raw}")
        parsed[key] = value
    return parsed


def load_json_payload(
    body_json: str | None, body_file: str | None
) -> dict[str, Any] | list[Any] | None:
    if body_json and body_file:
        raise ValueError("Use either --body-json or --body-file, not both")
    if body_json:
        value = json.loads(body_json)
        if not isinstance(value, (dict, list)):
            raise ValueError("--body-json must decode to an object or array")
        return value
    if body_file:
        with open(body_file, encoding="utf-8") as handle:
            value = json.load(handle)
        if not isinstance(value, (dict, list)):
            raise ValueError("--body-file content must be an object or array")
        return value
    return None


def resolve_dynamic_request(
    index: SchemaIndex,
    group: str,
    resource: str,
    action: str,
    *,
    object_id: int | None,
    query: dict[str, str],
    payload: dict[str, Any] | list[Any] | None,
) -> ResolvedRequest:
    action_lower = action.lower()
    method = ACTION_METHOD_MAP.get(action_lower, action.upper())

    resource_paths = index.resource_paths(group, resource)
    if resource_paths is None:
        raise ValueError(f"Resource not found: {group}/{resource}")

    detail_actions = {"get", "update", "patch", "delete"}
    needs_detail = action_lower in detail_actions

    if needs_detail:
        if object_id is None:
            raise ValueError(f"Action '{action_lower}' requires --id")
        if not resource_paths.detail_path:
            raise ValueError(f"Resource does not expose detail path: {group}/{resource}")
        path = resource_paths.detail_path.replace("{id}", str(object_id))
    else:
        if object_id is not None and resource_paths.detail_path and action_lower == "list":
            path = resource_paths.detail_path.replace("{id}", str(object_id))
        elif resource_paths.list_path:
            path = resource_paths.list_path
        else:
            raise ValueError(f"Resource does not expose list path: {group}/{resource}")

    return ResolvedRequest(method=method, path=path, query=query, payload=payload)


async def run_dynamic_command(
    client: NetBoxApiClient,
    index: SchemaIndex,
    group: str,
    resource: str,
    action: str,
    *,
    object_id: int | None,
    query_pairs: list[str],
    body_json: str | None,
    body_file: str | None,
) -> ApiResponse:
    query = parse_key_value_pairs(query_pairs)
    payload = load_json_payload(body_json, body_file)
    resolved = resolve_dynamic_request(
        index,
        group,
        resource,
        action,
        object_id=object_id,
        query=query,
        payload=payload,
    )
    return await client.request(
        resolved.method,
        resolved.path,
        query=resolved.query,
        payload=resolved.payload,
    )
