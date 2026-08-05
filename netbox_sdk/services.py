"""Service-layer helpers for resolving dynamic CLI requests from user input."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.exceptions import JsonPayloadError, PaginationError
from netbox_sdk.http_cache import QueryParams
from netbox_sdk.schema import SchemaIndex

logger = logging.getLogger(__name__)

ACTION_METHOD_MAP = {
    "list": "GET",
    "get": "GET",
    "create": "POST",
    "update": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
    "bulk-update": "PUT",
    "bulk-patch": "PATCH",
    "bulk-delete": "DELETE",
}

# Bulk actions route to the list path (no --id required).
_BULK_LIST_ACTIONS: frozenset[str] = frozenset({"bulk-update", "bulk-patch", "bulk-delete"})
# Detail actions always require --id and route to the detail path.
_DETAIL_ACTIONS: frozenset[str] = frozenset({"get", "update", "patch", "delete"})


class ResolvedRequest(BaseModel):
    """Normalized HTTP method, path, query string map, and JSON body for one dynamic call."""

    method: str
    path: str
    query: QueryParams
    payload: dict[str, Any] | list[Any] | None


def parse_key_value_pairs(values: list[str]) -> QueryParams:
    """Parse CLI ``key=value`` tokens into query parameters.

    Args:
        values: Raw strings from the CLI (e.g. ``["status=active"]``).

    Returns:
        Mapping of query keys to values. Repeated keys are preserved as lists
        so NetBox filters such as ``tag=foo&tag=bar`` remain expressible.

    Raises:
        ValueError: If any token is missing ``=`` or has an empty key.
    """
    parsed: QueryParams = {}
    for raw in values:
        if "=" not in raw:
            raise ValueError(f"Expected key=value format, got: {raw}")
        key, value = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Expected key=value format, got: {raw}")
        existing = parsed.get(key)
        if existing is None:
            parsed[key] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            parsed[key] = [existing, value]
    return parsed


def parse_header_pairs(values: list[str]) -> dict[str, str]:
    """Parse ``Header=Value`` or ``Header: Value`` CLI tokens into HTTP headers."""
    parsed: dict[str, str] = {}
    for raw in values:
        if "=" in raw:
            key, value = raw.split("=", 1)
        elif ":" in raw:
            key, value = raw.split(":", 1)
        else:
            raise ValueError(f"Expected header=value or 'Header: value' format, got: {raw}")
        key = key.strip()
        value = value.strip()
        if not key or "\r" in key or "\n" in key or "\r" in value or "\n" in value:
            raise ValueError(f"Expected header=value or 'Header: value' format, got: {raw}")
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
    query: QueryParams,
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

    if action_lower in _BULK_LIST_ACTIONS:
        # Bulk operations always target the list path; --id is not used.
        if not resource_paths.list_path:
            raise ValueError(f"Resource does not expose list path: {group}/{resource}")
        path = resource_paths.list_path
    elif action_lower in _DETAIL_ACTIONS:
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
    header_pairs: list[str] | None = None,
    body_json: str | None,
    body_file: str | None,
) -> ApiResponse:
    """Execute a schema-resolved request using the shared async HTTP client."""
    query = parse_key_value_pairs(query_pairs)
    headers = parse_header_pairs(header_pairs or [])
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
    request_kwargs: dict[str, Any] = {
        "query": resolved.query,
        "payload": resolved.payload,
    }
    if headers:
        request_kwargs["headers"] = headers
    return await client.request(resolved.method, resolved.path, **request_kwargs)


def _is_successful_page(response: ApiResponse, data: Any) -> bool:
    """True if a pagination page is a real paginated envelope, not an error body.

    A non-2xx status must never be treated as a valid page even if its body
    happens to parse as JSON and contain a ``results`` key.
    """
    return 200 <= response.status < 300 and isinstance(data, dict) and "results" in data


def _pagination_page_key(
    path: str, query: QueryParams
) -> tuple[str, tuple[tuple[str, tuple[str, ...]], ...]]:
    """Normalize a pagination target by path and parsed query parameters."""
    normalized_query = tuple(
        sorted(
            (key, tuple(value) if isinstance(value, list) else (value,))
            for key, value in query.items()
        )
    )
    return path, normalized_query


def _pagination_results(data: dict[str, Any], *, path: str) -> list[Any]:
    """Return a page's result list or raise a typed malformed-page error."""
    results = data.get("results")
    if not isinstance(results, list):
        raise PaginationError(f"Automatic pagination expected 'results' to be a list for {path}.")
    return results


def _pagination_next_url(data: dict[str, Any], *, path: str) -> str | None:
    """Return a valid next URL or raise a typed malformed-page error."""
    next_url = data.get("next")
    if next_url is not None and (not isinstance(next_url, str) or not next_url):
        raise PaginationError(
            f"Automatic pagination expected 'next' to be a URL or null for {path}."
        )
    return next_url


async def list_all_pages(
    client: NetBoxApiClient,
    index: SchemaIndex,
    group: str,
    resource: str,
    *,
    query_pairs: list[str],
    header_pairs: list[str] | None = None,
    max_records: int = 10000,
) -> ApiResponse:
    """Fetch all paginated pages for a list endpoint, following ``next`` links.

    The response envelope ``results`` arrays are concatenated into a single
    synthesised response with ``count`` equal to the total number of records
    retrieved (capped at ``max_records``).  Callers that don't need pagination
    should use :func:`run_dynamic_command` with action ``"list"`` instead.

    Args:
        client: Authenticated NetBox API client.
        index: Schema index for path resolution.
        group: API group (e.g. ``"dcim"``).
        resource: Resource name (e.g. ``"devices"``).
        query_pairs: Key=value filter strings (same format as CLI ``-q``).
        max_records: Upper bound on accumulated records. Defaults to 10 000.

    Returns:
        Synthesised :class:`~netbox_sdk.client.ApiResponse` whose body is a
        JSON object ``{"count": N, "next": null, "previous": null, "results": [...]}``.
        If the first response is not a paginated envelope the raw response is
        returned unchanged.

    Raises:
        PaginationError: If a page has malformed ``results``/``next`` values,
            repeats a previously visited path and query, or supplies a next
            link without adding any records.
    """
    query = parse_key_value_pairs(query_pairs)
    headers = parse_header_pairs(header_pairs or [])
    resolved = resolve_dynamic_request(
        index, group, resource, "list", object_id=None, query=query, payload=None
    )
    request_kwargs: dict[str, Any] = {
        "query": resolved.query,
        "payload": None,
    }
    if headers:
        request_kwargs["headers"] = headers
    response = await client.request(resolved.method, resolved.path, **request_kwargs)

    try:
        data = json.loads(response.text)
    except Exception:
        return response

    if not _is_successful_page(response, data):
        return response

    initial_results = _pagination_results(data, path=resolved.path)
    all_results: list[Any] = list(initial_results)
    next_url = _pagination_next_url(data, path=resolved.path)
    if not initial_results and next_url is not None:
        raise PaginationError(
            "Automatic pagination made no forward progress: "
            f"{resolved.path} returned no results but supplied a next link."
        )

    visited_pages = {_pagination_page_key(resolved.path, resolved.query)}

    while next_url and len(all_results) < max_records:
        parsed = urlparse(next_url)
        next_path = parsed.path
        parsed_query = parse_qs(parsed.query)
        next_query: QueryParams = {
            key: values if len(values) > 1 else values[0] for key, values in parsed_query.items()
        }
        page_key = _pagination_page_key(next_path, next_query)
        if page_key in visited_pages:
            raise PaginationError(
                f"Automatic pagination detected a repeated next link for {next_path}."
            )
        visited_pages.add(page_key)
        logger.debug(
            "following pagination next link",
            extra={
                "nbx_event": "list_all_pages_next",
                "next_path": next_path,
                "accumulated": len(all_results),
            },
        )
        request_kwargs = {
            "query": next_query,
            "payload": None,
        }
        if headers:
            request_kwargs["headers"] = headers
        response = await client.request("GET", next_path, **request_kwargs)
        try:
            data = json.loads(response.text)
        except Exception:
            # A later page failed after earlier pages already succeeded. Do
            # not synthesize a status-200 envelope from the partial results
            # collected so far — that would tell the caller pagination
            # completed when it did not. Propagate the raw failing response.
            return response
        if not _is_successful_page(response, data):
            return response
        page_results = _pagination_results(data, path=next_path)
        next_url = _pagination_next_url(data, path=next_path)
        if not page_results and next_url is not None:
            raise PaginationError(
                "Automatic pagination made no forward progress: "
                f"{next_path} returned no results but supplied a next link."
            )
        all_results.extend(page_results)

    combined: dict[str, Any] = {
        "count": len(all_results),
        "next": None,
        "previous": None,
        "results": all_results[:max_records],
    }
    return ApiResponse(status=200, text=json.dumps(combined), headers=response.headers)
