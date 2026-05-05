"""Runtime-generated FastAPI routes for the NetBox mock API."""

from __future__ import annotations

import inspect
import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Body, FastAPI, HTTPException, Path, Query, Response

from netbox_sdk.mock.schema_helpers import (
    RefResolver,
    _deep_merge,
    extract_items_schema,
    merge_with_schema_defaults,
    sample_value_for_schema,
    schema_fingerprint,
    schema_kind,
)
from netbox_sdk.mock.state import mock_store
from netbox_sdk.schema import load_openapi_schema
from netbox_sdk.versioning import SupportedNetBoxVersion

logger = logging.getLogger(__name__)

_SUPPORTED_METHODS: frozenset[str] = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})

_GENERATED_ROUTE_NAME_PREFIX = "netbox_mock__"
_ROUTE_STATE: dict[str, object] = {
    "route_count": 0,
    "path_count": 0,
    "method_count": 0,
    "schema_version": "",
}


@dataclass(frozen=True, slots=True)
class NetBoxRouteTopology:
    """Schema-derived metadata for a single NetBox API route."""

    path_template: str
    method: str
    operation: dict[str, Any]
    group: str | None
    resource: str | None
    is_list: bool  # /api/{group}/{resource}/
    is_detail: bool  # /api/{group}/{resource}/{id}/
    is_action: bool  # /api/{group}/{resource}/{id}/{action}/
    request_schema: dict[str, Any] | None
    response_schema: dict[str, Any] | None
    item_schema: dict[str, Any] | None  # For list endpoints: schema of one result
    list_path_template: str | None  # Corresponding list path


# ---------------------------------------------------------------------------
# Path classification helpers
# ---------------------------------------------------------------------------


def _classify_path(path: str) -> tuple[bool, bool, bool, str | None, str | None]:
    """Return (is_list, is_detail, is_action, group, resource) for a NetBox path."""
    parts = [p for p in path.split("/") if p]
    if not parts or parts[0] != "api":
        return False, False, False, None, None

    if len(parts) == 3:
        # /api/{group}/{resource}/
        group, resource = parts[1], parts[2]
        return True, False, False, group, resource

    if len(parts) == 4 and parts[3] == "{id}":
        # /api/{group}/{resource}/{id}/
        group, resource = parts[1], parts[2]
        return False, True, False, group, resource

    if len(parts) >= 5 and "{id}" in parts:
        # /api/{group}/{resource}/{id}/{action}/
        group, resource = parts[1], parts[2]
        return False, False, True, group, resource

    # Other special paths (e.g., /api/status/, /api/schema/)
    if len(parts) == 2:
        return False, False, False, None, None

    return False, False, False, None, None


def _list_path_for_detail(detail_path: str) -> str:
    """Return the list path for a given detail path."""
    parts = [p for p in detail_path.split("/") if p]
    # /api/{group}/{resource}/{id}/ -> /api/{group}/{resource}/
    list_parts = [p for p in parts if p != "{id}"]
    return "/" + "/".join(list_parts) + "/"


def _extract_request_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the JSON request body schema from an operation."""
    req_body = operation.get("requestBody")
    if not isinstance(req_body, dict):
        return None
    content = req_body.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema")
    return schema if isinstance(schema, dict) else None


def _extract_response_schema(operation: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the 2xx JSON response schema from an operation."""
    responses = operation.get("responses", {})
    for code in ("200", "201", "204"):
        resp = responses.get(code)
        if not isinstance(resp, dict):
            continue
        content = resp.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema")
        if isinstance(schema, dict):
            return schema
    return None


def _response_status(method: str, is_list: bool) -> int:
    """Return the expected HTTP status code for a method."""
    if method == "POST":
        return 201
    if method == "DELETE":
        return 204
    return 200


def _operation_id(path_template: str, method: str, operation: dict[str, Any]) -> str:
    op_id = operation.get("operationId")
    if isinstance(op_id, str) and op_id:
        return op_id
    slug = path_template.strip("/").replace("/", "__").replace("{", "").replace("}", "")
    return f"{method.lower()}__{slug}"


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------


def _build_object_url(request_base_url: str, path_template: str, obj_id: int) -> str:
    """Construct the canonical URL for a newly created object."""
    list_path = path_template if path_template.endswith("/") else path_template + "/"
    return f"{request_base_url.rstrip('/')}{list_path}{obj_id}/"


def _enrich_created_object(
    obj: dict[str, Any],
    *,
    obj_id: int,
    list_path: str,
    base_url: str = "http://mock.example.com",
) -> dict[str, Any]:
    """Add id/url/display_url/display fields to a newly created object."""
    result = deepcopy(obj)
    result.setdefault("id", obj_id)
    result.setdefault("url", f"{base_url.rstrip('/')}{list_path}{obj_id}/")
    result.setdefault("display_url", f"{base_url.rstrip('/')}{list_path}{obj_id}/")
    result.setdefault("display", obj.get("name") or obj.get("slug") or f"Object {obj_id}")
    return result


def _object_key(list_path: str, obj_id: int) -> str:
    """Compute the store key for a detail object."""
    return f"{list_path.rstrip('/')}/{obj_id}/"


def _list_collection_key(list_path: str) -> str:
    """Compute the store key for a list collection."""
    return list_path if list_path.endswith("/") else list_path + "/"


def _seed_list(
    item_schema: dict[str, Any] | None,
    resolver: RefResolver,
    *,
    collection_key: str,
) -> list[Any]:
    """Generate an initial empty list (NetBox mock starts empty for all collections)."""
    return []


def _paginate_results(
    items: list[Any],
    *,
    limit: int,
    offset: int,
    base_url: str,
    path: str,
) -> dict[str, Any]:
    """Wrap items in the NetBox offset-paginated response envelope."""
    total = len(items)
    page = items[offset : offset + limit]

    next_url = None
    if offset + limit < total:
        next_offset = offset + limit
        next_url = f"{base_url.rstrip('/')}{path}?limit={limit}&offset={next_offset}"

    previous_url = None
    if offset > 0:
        prev_offset = max(0, offset - limit)
        previous_url = f"{base_url.rstrip('/')}{path}?limit={limit}&offset={prev_offset}"

    return {
        "count": total,
        "next": next_url,
        "previous": previous_url,
        "results": page,
    }


def _paginate_results_cursor(
    items: list[Any],
    *,
    start: int,
    limit: int,
    base_url: str,
    path: str,
) -> dict[str, Any]:
    """Wrap items in the NetBox cursor-paginated response envelope (NetBox 4.6+)."""
    eligible = [
        item
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), int) and item["id"] >= start
    ]
    eligible.sort(key=lambda item: item["id"])
    page = eligible[:limit] if limit else eligible

    next_url = None
    if limit and len(eligible) > limit:
        last_id = page[-1]["id"]
        next_url = f"{base_url.rstrip('/')}{path}?start={last_id + 1}&limit={limit}"

    return {
        "count": None,
        "next": next_url,
        "previous": None,
        "results": page,
    }


def _filter_items(items: list[Any], query_values: dict[str, Any]) -> list[Any]:
    """Apply simple equality filter from query parameters."""
    if not query_values:
        return items
    result = []
    for item in items:
        if not isinstance(item, dict):
            result.append(item)
            continue
        match = True
        for key, value in query_values.items():
            if key not in item:
                continue
            item_val = item[key]
            # Handle nested status/label objects
            if isinstance(item_val, dict) and "value" in item_val:
                item_val = item_val["value"]
            if str(item_val) != str(value):
                match = False
                break
        if match:
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Endpoint builder
# ---------------------------------------------------------------------------


def _build_generated_endpoint(
    *,
    topology: NetBoxRouteTopology,
    resolver: RefResolver,
    schema_key: str,
    namespace: str | None,
) -> Any:
    """Build a dynamic async endpoint function for a single NetBox API route."""
    path_template = topology.path_template
    method = topology.method

    # Collect path parameters from the path template
    path_params: list[str] = []
    for segment in path_template.split("/"):
        if segment.startswith("{") and segment.endswith("}"):
            path_params.append(segment[1:-1])

    # Build query parameters from the OpenAPI operation
    query_params: list[tuple[str, str, bool]] = []  # (python_name, original_name, required)
    seen_params: set[str] = set(path_params)
    for param in topology.operation.get("parameters", []):
        if not isinstance(param, dict):
            continue
        location = param.get("in")
        name = param.get("name")
        if not isinstance(name, str) or not name:
            continue
        if location == "query":
            py_name = name.replace("-", "_").replace(".", "_")
            if py_name in seen_params:
                py_name = f"q_{py_name}"
            seen_params.add(py_name)
            required = bool(param.get("required", False))
            query_params.append((py_name, name, required))

    has_body = topology.request_schema is not None and method in ("POST", "PUT", "PATCH", "DELETE")

    # Build the inspect.Signature for FastAPI DI
    sig_params: list[inspect.Parameter] = []

    for pname in path_params:
        sig_params.append(
            inspect.Parameter(
                pname,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=int if pname == "id" else str,
                default=Path(...),
            )
        )

    for py_name, orig_name, required in query_params:
        alias = orig_name if py_name != orig_name else None
        sig_params.append(
            inspect.Parameter(
                py_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=str | None,
                default=Query(... if required else None, alias=alias),
            )
        )

    if has_body:
        sig_params.append(
            inspect.Parameter(
                "request_body",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Any,
                default=Body(None),
            )
        )

    async def generated_endpoint(**kwargs: Any) -> Any:
        store = mock_store(schema_key, namespace=namespace)

        # Extract path values
        path_values = {p: kwargs.pop(p, None) for p in path_params}
        obj_id = path_values.get("id")

        # Extract query values (for filtering / pagination)
        query_values: dict[str, Any] = {}
        for py_name, orig_name, _ in query_params:
            v = kwargs.get(py_name)
            if v is not None:
                query_values[orig_name] = v

        limit = int(query_values.pop("limit", 50))
        offset_raw = query_values.pop("offset", None)
        start_raw = query_values.pop("start", None)
        ordering_raw = query_values.pop("ordering", None)
        if start_raw is not None and offset_raw is not None:
            raise HTTPException(
                status_code=400,
                detail="'start' and 'offset' are mutually exclusive.",
            )
        if start_raw is not None and ordering_raw is not None:
            raise HTTPException(
                status_code=400,
                detail="Ordering cannot be specified in conjunction with cursor-based pagination.",
            )
        offset = int(offset_raw) if offset_raw is not None else 0
        try:
            start = int(start_raw) if start_raw is not None else None
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400, detail="Invalid 'start' parameter: must be a non-negative integer."
            ) from None
        if start is not None and start < 0:
            raise HTTPException(
                status_code=400, detail="Invalid 'start' parameter: must be a non-negative integer."
            )

        # Extract request body
        body = kwargs.pop("request_body", None)

        list_path = topology.list_path_template or topology.path_template
        list_key = _list_collection_key(list_path)

        # -------------------------------------------------------------------
        # GET list
        # -------------------------------------------------------------------
        if method == "GET" and topology.is_list:
            collection = store.get_collection(list_key)
            if collection is None:
                collection = _seed_list(topology.item_schema, resolver, collection_key=list_key)
                store.replace_collection(list_key, collection)
            filtered = _filter_items(collection, query_values)
            if start is not None:
                return _paginate_results_cursor(
                    filtered,
                    start=start,
                    limit=limit,
                    base_url="http://mock.example.com",
                    path=list_path,
                )
            return _paginate_results(
                filtered,
                limit=limit,
                offset=offset,
                base_url="http://mock.example.com",
                path=list_path,
            )

        # -------------------------------------------------------------------
        # GET detail
        # -------------------------------------------------------------------
        if method == "GET" and topology.is_detail:
            if obj_id is None:
                raise HTTPException(status_code=400, detail="Missing id parameter.")
            obj_key = _object_key(list_path, obj_id)
            if store.is_deleted(obj_key):
                raise HTTPException(status_code=404, detail="Not found.")
            obj = store.get_object(obj_key)
            if obj is None:
                # Auto-seed on first access
                obj = merge_with_schema_defaults(
                    topology.item_schema or topology.response_schema,
                    resolver=resolver,
                    seed=obj_key,
                )
                if isinstance(obj, dict):
                    obj = _enrich_created_object(obj, obj_id=int(obj_id), list_path=list_path)
                store.set_object(obj_key, obj)
            return obj

        # -------------------------------------------------------------------
        # GET action / other
        # -------------------------------------------------------------------
        if method == "GET":
            # Return a stub from the response schema
            stub = sample_value_for_schema(
                topology.response_schema,
                resolver=resolver,
                seed=f"get_{path_template}",
            )
            return stub if stub is not None else {}

        # -------------------------------------------------------------------
        # POST list (create / bulk create)
        # -------------------------------------------------------------------
        if method == "POST" and topology.is_list:
            is_bulk = isinstance(body, list)
            items = body if is_bulk else [body] if body is not None else [{}]
            created: list[dict[str, Any]] = []

            for item_body in items:
                new_id = store.next_id(list_key)
                new_obj = merge_with_schema_defaults(
                    topology.item_schema or topology.response_schema,
                    resolver=resolver,
                    seed=f"{list_key}_{new_id}",
                    override=item_body if isinstance(item_body, dict) else None,
                )
                if not isinstance(new_obj, dict):
                    new_obj = {}
                new_obj = _enrich_created_object(new_obj, obj_id=new_id, list_path=list_path)
                new_obj["id"] = new_id
                obj_key = _object_key(list_path, new_id)
                store.set_object(obj_key, new_obj)
                store.upsert_collection_member(list_key, obj_key, new_obj)
                created.append(new_obj)

            return created if is_bulk else created[0]

        # -------------------------------------------------------------------
        # PUT / PATCH detail (update)
        # -------------------------------------------------------------------
        if method in ("PUT", "PATCH") and topology.is_detail:
            if obj_id is None:
                raise HTTPException(status_code=400, detail="Missing id parameter.")
            obj_key = _object_key(list_path, obj_id)
            if store.is_deleted(obj_key):
                raise HTTPException(status_code=404, detail="Not found.")
            existing = store.get_object(obj_key)
            if existing is None:
                existing = {}

            if method == "PUT":
                updated = merge_with_schema_defaults(
                    topology.item_schema or topology.response_schema,
                    resolver=resolver,
                    seed=obj_key,
                    override=body if isinstance(body, dict) else None,
                )
                if not isinstance(updated, dict):
                    updated = {}
            else:  # PATCH
                updated = deepcopy(existing)
                if isinstance(body, dict):
                    updated = _deep_merge(updated, body)

            if isinstance(updated, dict):
                updated["id"] = int(obj_id)
                updated.setdefault("url", f"http://mock.example.com{obj_key}")
                updated.setdefault("display_url", f"http://mock.example.com{obj_key}")

            store.set_object(obj_key, updated)
            store.upsert_collection_member(list_key, obj_key, updated)
            return updated

        # -------------------------------------------------------------------
        # PUT / PATCH list (bulk update)
        # -------------------------------------------------------------------
        if method in ("PUT", "PATCH") and topology.is_list:
            if not isinstance(body, list):
                raise HTTPException(status_code=400, detail="Bulk update requires a list.")
            updated_items: list[dict[str, Any]] = []
            for item_body in body:
                if not isinstance(item_body, dict):
                    continue
                item_id = item_body.get("id")
                if item_id is None:
                    continue
                obj_key = _object_key(list_path, item_id)
                existing = store.get_object(obj_key) or {}
                if method == "PUT":
                    updated = merge_with_schema_defaults(
                        topology.item_schema,
                        resolver=resolver,
                        seed=obj_key,
                        override=item_body,
                    )
                    if not isinstance(updated, dict):
                        updated = {}
                else:
                    updated = _deep_merge(existing, item_body)
                if isinstance(updated, dict):
                    updated["id"] = int(item_id)
                store.set_object(obj_key, updated)
                store.upsert_collection_member(list_key, obj_key, updated)
                updated_items.append(updated)
            return updated_items

        # -------------------------------------------------------------------
        # DELETE detail
        # -------------------------------------------------------------------
        if method == "DELETE" and topology.is_detail:
            if obj_id is None:
                raise HTTPException(status_code=400, detail="Missing id parameter.")
            obj_key = _object_key(list_path, obj_id)
            if store.is_deleted(obj_key):
                raise HTTPException(status_code=404, detail="Not found.")
            store.delete_collection_member(list_key, obj_key)
            store.delete_object(obj_key)
            return Response(status_code=204)

        # -------------------------------------------------------------------
        # DELETE list (bulk delete)
        # -------------------------------------------------------------------
        if method == "DELETE" and topology.is_list:
            if isinstance(body, list):
                for item in body:
                    if isinstance(item, dict):
                        item_id = item.get("id")
                        if item_id is not None:
                            obj_key = _object_key(list_path, item_id)
                            store.delete_collection_member(list_key, obj_key)
                            store.delete_object(obj_key)
            return Response(status_code=204)

        # -------------------------------------------------------------------
        # Fallback action endpoints
        # -------------------------------------------------------------------
        stub = sample_value_for_schema(
            topology.response_schema,
            resolver=resolver,
            seed=f"{method.lower()}_{path_template}",
        )
        return stub if stub is not None else {}

    # Wire up the signature for FastAPI DI
    generated_endpoint.__name__ = f"{_GENERATED_ROUTE_NAME_PREFIX}{method.lower()}__{_operation_id(path_template, method, topology.operation)}"
    generated_endpoint.__qualname__ = generated_endpoint.__name__
    # DELETE endpoints must not declare a return type (no body for 204)
    return_annotation = None if method == "DELETE" else Any
    generated_endpoint.__signature__ = inspect.Signature(
        parameters=sig_params,
        return_annotation=return_annotation,
    )
    return generated_endpoint


# ---------------------------------------------------------------------------
# Main registration function
# ---------------------------------------------------------------------------


def register_netbox_mock_routes(
    app: FastAPI | APIRouter,
    *,
    version: SupportedNetBoxVersion = "4.5",
    openapi_document: dict[str, Any] | None = None,
    namespace: str | None = None,
    custom_mock_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Register all NetBox mock routes from the bundled OpenAPI spec.

    Iterates every path/method in the OpenAPI document and registers a
    dynamically generated ``async def`` endpoint on *app* via
    ``app.add_api_route()``.

    Args:
        app: FastAPI app or APIRouter to register routes on.
        version: NetBox release line to load the bundled schema for.
        openapi_document: Pre-loaded OpenAPI document dict (skips disk load).
        namespace: State isolation namespace (for parallel test processes).
        custom_mock_data: Dict of ``{path_template: initial_data}`` to seed.

    Returns:
        Stats dict: ``{route_count, path_count, method_count, schema_version}``.
    """
    document = openapi_document or load_openapi_schema(version=version)
    doc_fingerprint = schema_fingerprint(document)
    components_schemas = document.get("components", {}).get("schemas", {})
    resolver = RefResolver(components_schemas)
    schema_version = document.get("info", {}).get("version", version)

    path_items: dict[str, dict[str, Any]] = {
        path: item for path, item in (document.get("paths") or {}).items() if isinstance(item, dict)
    }

    # Pre-seed custom mock data into the store
    if custom_mock_data:
        store = mock_store(doc_fingerprint, namespace=namespace)
        for path_key, data in custom_mock_data.items():
            if isinstance(data, list):
                collection_key = path_key if path_key.endswith("/") else path_key + "/"
                store.replace_collection(collection_key, data)
            else:
                store.set_object(path_key, data)

    route_count = 0
    method_count = 0
    route_names: set[str] = set()

    for path_template, path_item in sorted(path_items.items()):
        for method_lower, operation in sorted(path_item.items()):
            method = method_lower.upper()
            if method not in _SUPPORTED_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            is_list, is_detail, is_action, group, resource = _classify_path(path_template)

            # Determine the list path for this route
            if is_detail or is_action:
                list_path = _list_path_for_detail(path_template)
            else:
                list_path = path_template

            request_schema = _extract_request_schema(operation)
            response_schema = _extract_response_schema(operation)

            # Resolve item schema for list endpoints
            item_schema: dict[str, Any] | None = None
            if response_schema:
                resolved_resp = resolver.resolve(response_schema)
                if schema_kind(response_schema, resolver) == "paginated_list":
                    item_schema = extract_items_schema(response_schema, resolver)
                elif schema_kind(response_schema, resolver) in ("object", "array"):
                    item_schema = (
                        resolved_resp
                        if resolved_resp.get("type") != "array"
                        else resolved_resp.get("items")
                    )

            topology = NetBoxRouteTopology(
                path_template=path_template,
                method=method,
                operation=operation,
                group=group,
                resource=resource,
                is_list=is_list,
                is_detail=is_detail,
                is_action=is_action,
                request_schema=request_schema,
                response_schema=response_schema,
                item_schema=item_schema,
                list_path_template=list_path if (is_detail or is_action) else None,
            )

            endpoint = _build_generated_endpoint(
                topology=topology,
                resolver=resolver,
                schema_key=doc_fingerprint,
                namespace=namespace,
            )

            op_id = _operation_id(path_template, method, operation)
            route_name = f"{_GENERATED_ROUTE_NAME_PREFIX}{method.lower()}__{op_id}"

            # Determine status code, response class, and response model
            status_code = _response_status(method, is_list)
            is_no_body = method == "DELETE"

            kwargs: dict[str, Any] = dict(
                path=path_template,
                endpoint=endpoint,
                methods=[method],
                name=route_name,
                summary=operation.get("summary"),
                description=operation.get("description"),
                tags=operation.get("tags", ["netbox mock"]),
                status_code=status_code,
            )
            if is_no_body:
                # 204 must have no response body; suppress model inference
                kwargs["response_class"] = Response
                kwargs["response_model"] = None

            app.add_api_route(**kwargs)
            route_names.add(route_name)
            route_count += 1
            method_count += 1

    _ROUTE_STATE["route_count"] = route_count
    _ROUTE_STATE["path_count"] = len(path_items)
    _ROUTE_STATE["method_count"] = method_count
    _ROUTE_STATE["schema_version"] = schema_version

    # Invalidate FastAPI's cached OpenAPI schema so it regenerates with new routes
    if hasattr(app, "openapi_schema"):
        app.openapi_schema = None

    logger.info(
        "Registered NetBox mock routes",
        extra={
            "nbx_event": "mock_routes_registered",
            "route_count": route_count,
            "schema_version": schema_version,
        },
    )

    return {
        "route_count": route_count,
        "path_count": len(path_items),
        "method_count": method_count,
        "schema_version": schema_version,
    }


def netbox_mock_route_state() -> dict[str, object]:
    """Return metadata about the currently mounted mock route set."""
    return {
        "route_count": _ROUTE_STATE["route_count"],
        "path_count": _ROUTE_STATE["path_count"],
        "method_count": _ROUTE_STATE["method_count"],
        "schema_version": _ROUTE_STATE["schema_version"],
    }


__all__ = [
    "NetBoxRouteTopology",
    "register_netbox_mock_routes",
    "netbox_mock_route_state",
]
