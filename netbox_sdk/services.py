"""Service-layer helpers for resolving dynamic CLI requests from user input."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.exceptions import JsonPayloadError
from netbox_sdk.schema import SchemaIndex

logger = logging.getLogger(__name__)

ACTION_METHOD_MAP = {
    "list": "GET",
    "get": "GET",
    "create": "POST",
    "update": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}


class ResolvedRequest(BaseModel):
    """Normalized HTTP method, path, query string map, and JSON body for one dynamic call."""

    method: str
    path: str
    query: dict[str, str]
    payload: dict[str, Any] | list[Any] | None


def parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    """Parse CLI ``key=value`` tokens into a query parameter dict.

    Args:
        values: Raw strings from the CLI (e.g. ``["status=active"]``).

    Returns:
        Mapping of query keys to values.

    Raises:
        ValueError: If any token is missing ``=`` or has an empty key.
    """
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
    """Load request JSON from inline string or file path (mutually exclusive).

    Args:
        body_json: Raw JSON object/array as a string.
        body_file: Path to a UTF-8 JSON file containing an object or array.

    Returns:
        Parsed payload, or ``None`` if neither source is set.

    Raises:
        JsonPayloadError: If both sources are set, the file is missing/unreadable,
            JSON is invalid, or the decoded value is not a JSON object or array.
    """
    if body_json and body_file:
        raise JsonPayloadError("Use either --body-json or --body-file, not both")
    if body_json:
        try:
            value = json.loads(body_json)
        except json.JSONDecodeError:
            logger.debug(
                "body-json decode failed",
                extra={"nbx_event": "payload_json_error", "source": "inline"},
            )
            raise
        if not isinstance(value, (dict, list)):
            raise JsonPayloadError("--body-json must decode to an object or array")
        return value
    if body_file:
        path = Path(body_file)
        if not path.exists():
            logger.debug(
                "body-file not found",
                extra={"nbx_event": "payload_file_missing", "path": str(path)},
            )
            raise FileNotFoundError(2, "No such file or directory", str(path))
        if not path.is_file():
            logger.debug(
                "body-file path is not a regular file",
                extra={"nbx_event": "payload_file_not_file", "path": str(path)},
            )
            raise JsonPayloadError(f"--body-file is not a file: {path}")
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning(
                "body-file read failed",
                extra={"nbx_event": "payload_file_read_error", "path": str(path)},
            )
            raise JsonPayloadError(f"Cannot read --body-file {path}: {exc}") from exc
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.debug(
                "body-file decode failed",
                extra={"nbx_event": "payload_json_error", "source": "file", "path": str(path)},
            )
            raise JsonPayloadError(f"--body-file content is not valid JSON: {path}") from exc
        if not isinstance(value, (dict, list)):
            raise JsonPayloadError("--body-file content must be an object or array")
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
    """Map OpenAPI index + user action to method, path, query, and body.

    Raises:
        ValueError: If the resource or action combination is invalid (missing paths, missing id).
    """
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

    logger.debug(
        "resolved dynamic request",
        extra={
            "nbx_event": "resolve_dynamic_request",
            "group": group,
            "resource": resource,
            "method": method,
            "path": path,
        },
    )
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
    """Execute a schema-resolved request using the shared async HTTP client."""
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
