"""Runtime-generated FastAPI routes for the NetBox mock API."""

from __future__ import annotations

import inspect
import json
import logging
import re
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from fastapi import APIRouter, Body, FastAPI, HTTPException, Path, Query, Response
from fastapi.responses import JSONResponse

from netbox_sdk.mock.schema_helpers import (
    RefResolver,
    _deep_merge,
    extract_items_schema,
    merge_with_schema_defaults,
    sample_value_for_schema,
    schema_fingerprint,
    schema_kind,
)
from netbox_sdk.mock.state import ThreadSafeMockStore, mock_store
from netbox_sdk.schema import load_openapi_schema
from netbox_sdk.versioning import DEFAULT_NETBOX_VERSION, SupportedNetBoxVersion

logger = logging.getLogger(__name__)

_SUPPORTED_METHODS: frozenset[str] = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})

_GENERATED_ROUTE_NAME_PREFIX = "netbox_mock__"
_ROUTE_STATE_ATTRIBUTE = "_netbox_mock_route_state"


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
    supports_background: bool = False


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


def _schema_allows_array(schema: dict[str, Any] | None) -> bool:
    """Return whether an inline request schema accepts an array payload."""
    if not isinstance(schema, dict):
        return False
    if schema.get("type") == "array":
        return True
    return any(
        _schema_allows_array(variant)
        for keyword in ("oneOf", "anyOf")
        for variant in schema.get(keyword, [])
        if isinstance(variant, dict)
    )


def _payload_item_schema(
    request_schema: dict[str, Any] | None,
    resolver: RefResolver,
    *,
    bulk: bool,
) -> dict[str, Any]:
    """Select the object schema for one singular or bulk request item."""
    if not isinstance(request_schema, dict):
        return {}
    variants = next(
        (
            value
            for keyword in ("oneOf", "anyOf")
            if isinstance((value := request_schema.get(keyword)), list)
        ),
        [request_schema],
    )
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        resolved = resolver.resolve(variant)
        if bulk and resolved.get("type") == "array":
            items = resolved.get("items")
            return resolver.resolve(items) if isinstance(items, dict) else {}
        if not bulk and (resolved.get("type") == "object" or "properties" in resolved):
            return resolved
    resolved = resolver.resolve(request_schema)
    if bulk and resolved.get("type") == "array" and isinstance(resolved.get("items"), dict):
        return resolver.resolve(resolved["items"])
    return resolved


def _json_identity(value: Any) -> str:
    """Return a stable identity for JSON values used by uniqueness checks."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _value_validation_errors(
    value: Any,
    schema: dict[str, Any],
    resolver: RefResolver,
) -> list[str]:
    """Validate one value against the OpenAPI constraints used by NetBox writes."""
    composition_errors = _composition_validation_errors(value, schema, resolver)
    if composition_errors is not None:
        return composition_errors

    resolved = resolver.resolve_property(schema)
    null_errors = _null_validation_errors(value, resolved)
    if null_errors is not None:
        return null_errors
    enum = resolved.get("enum")
    if isinstance(enum, list) and value not in enum:
        return [f"{value!r} is not a valid choice."]
    schema_type = resolved.get("type")
    if not isinstance(schema_type, str):
        return []
    type_error = _type_validation_error(value, schema_type)
    if type_error is not None:
        return [type_error]
    validator = {
        "string": lambda: _string_validation_errors(value, resolved),
        "integer": lambda: _number_validation_errors(value, resolved),
        "number": lambda: _number_validation_errors(value, resolved),
        "array": lambda: _array_validation_errors(value, resolved, resolver),
        "object": lambda: _object_errors(value, resolved, resolver),
    }.get(schema_type)
    return validator() if validator is not None else []


def _composition_validation_errors(
    value: Any,
    schema: dict[str, Any],
    resolver: RefResolver,
) -> list[str] | None:
    """Validate oneOf/anyOf schemas, or return None when no composition exists."""
    for keyword in ("oneOf", "anyOf"):
        variants = schema.get(keyword)
        if isinstance(variants, list):
            if any(
                not _value_validation_errors(value, variant, resolver)
                for variant in variants
                if isinstance(variant, dict)
            ):
                return []
            return ["Does not match any allowed representation."]
    return None


def _null_validation_errors(value: Any, schema: dict[str, Any]) -> list[str] | None:
    """Validate nullability, or return None for non-null values."""
    if value is not None:
        return None
    enum = schema.get("enum")
    accepts_null = (
        schema.get("nullable")
        or schema.get("type") == "null"
        or isinstance(enum, list)
        and None in enum
    )
    return [] if accepts_null else ["May not be null."]


def _type_validation_error(value: Any, schema_type: Any) -> str | None:
    """Return a primitive type error, or None for unconstrained/composite types."""
    expected_types: dict[str, type[Any] | tuple[type[Any], ...]] = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    if not isinstance(schema_type, str):
        return None
    expected = expected_types.get(schema_type)
    if expected is not None and (
        not isinstance(value, expected)
        or schema_type in {"integer", "number"}
        and isinstance(value, bool)
    ):
        return f"Expected {schema_type}."
    return None


def _object_errors(
    value: Any,
    schema: dict[str, Any],
    resolver: RefResolver,
) -> list[str]:
    """Adapt field-keyed object errors to the scalar validator contract."""
    nested = _object_validation_errors(value, schema, resolver)
    return [f"Invalid object: {nested}"] if nested else []


def _string_validation_errors(value: str, schema: dict[str, Any]) -> list[str]:
    """Validate JSON Schema string length and pattern constraints."""
    errors: list[str] = []
    if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
        errors.append(f"Ensure this field has at least {schema['minLength']} characters.")
    if isinstance(schema.get("maxLength"), int) and len(value) > schema["maxLength"]:
        errors.append(f"Ensure this field has no more than {schema['maxLength']} characters.")
    pattern = schema.get("pattern")
    if isinstance(pattern, str) and re.search(pattern, value) is None:
        errors.append("Value does not match the required pattern.")
    return errors


def _number_validation_errors(value: int | float, schema: dict[str, Any]) -> list[str]:
    """Validate JSON Schema numeric range constraints."""
    errors: list[str] = []
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_minimum = schema.get("exclusiveMinimum")
    exclusive_maximum = schema.get("exclusiveMaximum")
    if isinstance(minimum, (int, float)):
        violates_minimum = value <= minimum if exclusive_minimum is True else value < minimum
        if violates_minimum:
            operator = "greater than" if exclusive_minimum is True else "greater than or equal to"
            errors.append(f"Ensure this value is {operator} {minimum}.")
    if isinstance(maximum, (int, float)):
        violates_maximum = value >= maximum if exclusive_maximum is True else value > maximum
        if violates_maximum:
            operator = "less than" if exclusive_maximum is True else "less than or equal to"
            errors.append(f"Ensure this value is {operator} {maximum}.")
    return errors


def _array_validation_errors(
    value: list[Any],
    schema: dict[str, Any],
    resolver: RefResolver,
) -> list[str]:
    """Validate JSON Schema array size, uniqueness, and item constraints."""
    errors: list[str] = []
    if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
        errors.append(f"Ensure this list has at least {schema['minItems']} items.")
    if isinstance(schema.get("maxItems"), int) and len(value) > schema["maxItems"]:
        errors.append(f"Ensure this list has no more than {schema['maxItems']} items.")
    if schema.get("uniqueItems") and len({_json_identity(item) for item in value}) != len(value):
        errors.append("List items must be unique.")
    item_schema = schema.get("items")
    if isinstance(item_schema, dict):
        for index, item in enumerate(value):
            errors.extend(
                f"Item {index}: {message}"
                for message in _value_validation_errors(item, item_schema, resolver)
            )
    return errors


def _object_validation_errors(
    item: dict[str, Any],
    schema: dict[str, Any],
    resolver: RefResolver,
) -> dict[str, list[str]]:
    """Return field-keyed errors for one object request schema."""
    resolved = resolver.resolve(schema)
    properties = resolved.get("properties", {})
    required = resolved.get("required", [])
    errors = {
        name: ["This field is required."]
        for name in required
        if isinstance(name, str) and name not in item
    }
    if not isinstance(properties, dict):
        return errors
    for name, value in item.items():
        property_schema = properties.get(name)
        if not isinstance(property_schema, dict):
            continue
        field_errors = _value_validation_errors(value, property_schema, resolver)
        if field_errors:
            errors[name] = field_errors
    return errors


_UNIQUE_FIELDS_BY_PATH: dict[str, tuple[str, ...]] = {
    "/api/dcim/sites/": ("slug",),
    "/api/extras/custom-fields/": ("name",),
    "/api/extras/custom-field-choice-sets/": ("name",),
}


def _uniqueness_errors(
    request: _GeneratedRequest,
    items: list[Any],
) -> dict[int, dict[str, list[str]]]:
    """Model unique fields that OpenAPI cannot express for representative resources."""
    fields = _UNIQUE_FIELDS_BY_PATH.get(request.list_path, ())
    if not fields:
        return {}
    existing = request.store.get_collection(request.list_key) or []
    errors: dict[int, dict[str, list[str]]] = {}
    for field in fields:
        seen: dict[str, int] = {}
        for index, item in enumerate(items):
            if not isinstance(item, dict) or field not in item:
                continue
            identity = _json_identity(item[field])
            item_id = item.get("id")
            duplicate_existing = any(
                isinstance(row, dict) and row.get(field) == item[field] and row.get("id") != item_id
                for row in existing
            )
            if duplicate_existing or identity in seen:
                errors.setdefault(index, {}).setdefault(field, []).append(
                    "An object with this value already exists."
                )
            seen.setdefault(identity, index)
    return errors


def _service_representation_errors(
    item: dict[str, Any],
    *,
    list_path: str,
) -> dict[str, list[str]]:
    """Reject conflicting NetBox 4.7 service port representations."""
    if list_path not in _SERVICE_LIST_PATHS or "port_mappings" not in item:
        return {}
    if "protocol" not in item and "ports" not in item:
        return {}
    mappings = item.get("port_mappings")
    implied_protocol, implied_ports = _legacy_service_fields(
        mappings if isinstance(mappings, list) else []
    )
    protocol_conflicts = "protocol" in item and _service_protocol_value(item["protocol"]) != (
        implied_protocol
    )
    ports_conflict = "ports" in item and item["ports"] != implied_ports
    if not protocol_conflicts and not ports_conflict:
        return {}
    return {
        "non_field_errors": [
            "The legacy protocol/ports fields conflict with port_mappings and are ambiguous."
        ]
    }


def _entry_errors(
    request: _GeneratedRequest,
    item: Any,
    *,
    bulk: bool,
    require_id: bool,
) -> dict[str, list[str]]:
    """Validate one write item before any state mutation."""
    if not isinstance(item, dict):
        return {"non_field_errors": ["Expected an object."]}
    if request.topology.method == "DELETE":
        errors: dict[str, list[str]] = {}
    else:
        schema = _payload_item_schema(request.topology.request_schema, request.resolver, bulk=bulk)
        errors = _object_validation_errors(item, schema, request.resolver)
    if require_id and (
        not isinstance(item.get("id"), int) or isinstance(item.get("id"), bool) or item["id"] < 1
    ):
        errors["id"] = ["A positive integer ID is required."]
    for name, messages in _service_representation_errors(
        item,
        list_path=request.list_path,
    ).items():
        errors.setdefault(name, []).extend(messages)
    return errors


def _bulk_entry_errors(
    request: _GeneratedRequest,
    body: list[Any],
    *,
    require_id: bool,
) -> list[dict[str, Any]]:
    """Return NetBox 4.7-style schema and model errors for bulk entries."""
    per_index = _uniqueness_errors(request, body)
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(body):
        entry = _entry_errors(request, item, bulk=True, require_id=require_id)
        for name, messages in per_index.get(index, {}).items():
            entry.setdefault(name, []).extend(messages)
        if entry:
            errors.append({"index": index, "errors": entry})
    return errors


def _bulk_error_response(
    errors: list[dict[str, Any]], *, total: int, action: str
) -> JSONResponse | None:
    """Build a structured bulk error response when validation failed."""
    if not errors:
        return None
    return JSONResponse(
        status_code=400,
        content={
            "detail": f"{len(errors)} of {total} objects could not be {action}.",
            "errors": errors,
        },
    )


def _background_job_response(request: _GeneratedRequest) -> JSONResponse:
    """Persist a deterministic queued job whose mutation runs after polling."""
    job_list_path = "/api/core/jobs/"
    job_id = request.store.next_id(job_list_path)
    job_url = f"http://mock.example.com{job_list_path}{job_id}/"
    record = {
        "id": job_id,
        "url": job_url,
        "display_url": job_url,
        "display": f"Background bulk {request.topology.method} job {job_id}",
        "name": f"Background bulk {request.topology.method}",
        "status": "pending",
        "error": "",
    }

    def operation() -> tuple[bool, Any]:
        result = _dispatch_generated_request(replace(request, use_background=False))
        if isinstance(result, Response) and result.status_code >= 400:
            try:
                return False, json.loads(bytes(result.body))
            except (AttributeError, json.JSONDecodeError, UnicodeDecodeError):
                return False, f"HTTP {result.status_code}"
        return True, None

    request.store.queue_background_job(
        job_id,
        record=record,
        object_key=_object_key(job_list_path, job_id),
        collection_key=job_list_path,
        operation=operation,
    )
    return JSONResponse(
        status_code=202,
        content={"job": record},
    )


def _affirmative(value: Any) -> bool:
    """Return whether a query value enables an opt-in boolean feature."""
    return value is True or str(value).strip().lower() in {"1", "true"}


_SERVICE_LIST_PATHS = frozenset({"/api/ipam/services/", "/api/ipam/service-templates/"})
_PROTOCOL_LABELS = {"tcp": "TCP", "udp": "UDP", "sctp": "SCTP"}


def _service_protocol_value(value: Any) -> str | None:
    """Extract a legacy service protocol from its write or read representation."""
    if isinstance(value, dict):
        value = value.get("value")
    return value if isinstance(value, str) and value in _PROTOCOL_LABELS else None


def _legacy_service_fields(port_mappings: list[Any]) -> tuple[str | None, list[int] | None]:
    """Derive the legacy single-protocol representation from port mappings."""
    parsed: list[tuple[str, int]] = []
    for mapping in port_mappings:
        if not isinstance(mapping, str):
            return None, None
        protocol, separator, port = mapping.partition("/")
        if not separator or protocol not in _PROTOCOL_LABELS or not port.isdigit():
            return None, None
        parsed.append((protocol, int(port)))
    protocols = {protocol for protocol, _port in parsed}
    if len(protocols) != 1:
        return None, None
    return parsed[0][0], [port for _protocol, port in parsed]


def _normalize_service_response(
    obj: dict[str, Any], *, list_path: str, write_payload: dict[str, Any] | None
) -> dict[str, Any]:
    """Render the NetBox 4.7 service read shape after either accepted write shape."""
    if list_path not in _SERVICE_LIST_PATHS:
        return obj
    result = deepcopy(obj)
    source = write_payload or {}
    if "port_mappings" in source:
        mappings = source.get("port_mappings")
    elif "protocol" in source or "ports" in source:
        protocol = _service_protocol_value(source.get("protocol", result.get("protocol")))
        ports = source.get("ports", result.get("ports"))
        mappings = (
            [f"{protocol}/{port}" for port in ports]
            if protocol is not None and isinstance(ports, list)
            else []
        )
    else:
        mappings = result.get("port_mappings")
    mappings = mappings if isinstance(mappings, list) else []
    result["port_mappings"] = deepcopy(mappings)
    protocol, ports = _legacy_service_fields(mappings)
    result["protocol"] = (
        {"value": protocol, "label": _PROTOCOL_LABELS[protocol]} if protocol is not None else None
    )
    result["ports"] = ports
    return result


def _custom_field_type(definition: dict[str, Any]) -> str | None:
    """Extract a custom field type from its write or read representation."""
    value = definition.get("type")
    if isinstance(value, dict):
        value = value.get("value")
    return value if isinstance(value, str) else None


def _custom_field_choice_labels(
    store: ThreadSafeMockStore, definition: dict[str, Any]
) -> dict[str, str]:
    """Return labels declared by a mock custom field's choice set."""
    choice_set = definition.get("choice_set")
    choice_set_id = choice_set.get("id") if isinstance(choice_set, dict) else choice_set
    rows = store.get_collection("/api/extras/custom-field-choice-sets/") or []
    selected = next(
        (row for row in rows if isinstance(row, dict) and row.get("id") == choice_set_id),
        {},
    )
    choices = selected.get("extra_choices", []) if isinstance(selected, dict) else []
    return {
        str(pair[0]): str(pair[1]) for pair in choices if isinstance(pair, list) and len(pair) == 2
    }


def _choice_object(value: Any, labels: dict[str, str]) -> Any:
    """Render one NetBox 4.7 selection value as a value/label object."""
    if isinstance(value, dict) and set(value) == {"value", "label"}:
        return deepcopy(value)
    return {"value": value, "label": labels.get(str(value), str(value))}


def _serialize_custom_field_choices(
    obj: dict[str, Any], store: ThreadSafeMockStore
) -> dict[str, Any]:
    """Render configured selection custom fields in the NetBox 4.7 read shape."""
    custom_fields = obj.get("custom_fields")
    if not isinstance(custom_fields, dict):
        return obj
    definitions = store.get_collection("/api/extras/custom-fields/") or []
    by_name = {
        row["name"]: row
        for row in definitions
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    result = deepcopy(obj)
    rendered = result["custom_fields"]
    for name, value in custom_fields.items():
        definition = by_name.get(name)
        if definition is None:
            continue
        field_type = _custom_field_type(definition)
        if field_type not in {"select", "multiselect"}:
            continue
        if value is None:
            rendered[name] = None
            continue
        labels = _custom_field_choice_labels(store, definition)
        if field_type == "multiselect" and isinstance(value, list):
            rendered[name] = [_choice_object(item, labels) for item in value]
        else:
            rendered[name] = _choice_object(value, labels)
    return result


def _normalize_response_object(
    obj: dict[str, Any],
    *,
    list_path: str,
    write_payload: dict[str, Any] | None,
    store: ThreadSafeMockStore,
) -> dict[str, Any]:
    """Apply response-only NetBox 4.7 representations before storage."""
    result = _normalize_service_response(obj, list_path=list_path, write_payload=write_payload)
    return _serialize_custom_field_choices(result, store)


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


@dataclass(slots=True)
class _GeneratedRequest:
    """Parsed runtime inputs plus the static topology for one generated route."""

    topology: NetBoxRouteTopology
    resolver: RefResolver
    store: ThreadSafeMockStore
    obj_id: Any
    query_values: dict[str, Any]
    limit: int
    offset: int
    start: int | None
    body: Any
    list_path: str
    list_key: str
    use_background: bool


def _path_parameter_names(path_template: str) -> list[str]:
    """Extract FastAPI parameter names from a route template."""
    return [
        segment[1:-1]
        for segment in path_template.split("/")
        if segment.startswith("{") and segment.endswith("}")
    ]


def _query_parameter_specs(
    topology: NetBoxRouteTopology, path_params: list[str]
) -> tuple[list[tuple[str, str, bool]], set[str]]:
    """Return collision-safe Python/query names declared by an operation."""
    query_params: list[tuple[str, str, bool]] = []
    seen_params = set(path_params)
    for param in topology.operation.get("parameters", []):
        if not isinstance(param, dict) or param.get("in") != "query":
            continue
        name = param.get("name")
        if not isinstance(name, str) or not name:
            continue
        py_name = name.replace("-", "_").replace(".", "_")
        if py_name in seen_params:
            py_name = f"q_{py_name}"
        seen_params.add(py_name)
        query_params.append((py_name, name, bool(param.get("required", False))))
    return query_params, seen_params


def _endpoint_signature_parameters(
    topology: NetBoxRouteTopology,
    path_params: list[str],
    query_params: list[tuple[str, str, bool]],
    seen_params: set[str],
) -> list[inspect.Parameter]:
    """Build the signature FastAPI uses for dependency injection."""
    parameters = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            annotation=int if name == "id" else str,
            default=Path(...),
        )
        for name in path_params
    ]
    for py_name, original_name, required in query_params:
        alias = original_name if py_name != original_name else None
        parameters.append(
            inspect.Parameter(
                py_name,
                inspect.Parameter.KEYWORD_ONLY,
                annotation=str | None,
                default=Query(... if required else None, alias=alias),
            )
        )
    if topology.supports_background and "background" not in seen_params:
        parameters.append(
            inspect.Parameter(
                "background",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=str | None,
                default=Query(None),
            )
        )
    if topology.request_schema is not None and topology.method in {
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }:
        parameters.append(
            inspect.Parameter(
                "request_body",
                inspect.Parameter.KEYWORD_ONLY,
                annotation=Any,
                default=Body(None),
            )
        )
    return parameters


def _extract_query_values(
    kwargs: dict[str, Any], query_params: list[tuple[str, str, bool]]
) -> dict[str, Any]:
    """Map generated Python argument names back to OpenAPI query names."""
    return {
        original_name: kwargs[py_name]
        for py_name, original_name, _required in query_params
        if kwargs.get(py_name) is not None
    }


def _parse_pagination(query_values: dict[str, Any]) -> tuple[int, int, int | None]:
    """Remove and validate pagination controls, leaving only resource filters."""
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
            status_code=400,
            detail="Invalid 'start' parameter: must be a non-negative integer.",
        ) from None
    if start is not None and start < 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid 'start' parameter: must be a non-negative integer.",
        )
    return limit, offset, start


def _parse_generated_request(
    kwargs: dict[str, Any],
    *,
    topology: NetBoxRouteTopology,
    resolver: RefResolver,
    schema_key: str,
    namespace: str | None,
    path_params: list[str],
    query_params: list[tuple[str, str, bool]],
) -> _GeneratedRequest:
    """Parse one generated endpoint invocation into its dispatch state."""
    store = mock_store(schema_key, namespace=namespace)
    path_values = {name: kwargs.pop(name, None) for name in path_params}
    query_values = _extract_query_values(kwargs, query_params)
    limit, offset, start = _parse_pagination(query_values)
    list_path = topology.list_path_template or topology.path_template
    return _GeneratedRequest(
        topology=topology,
        resolver=resolver,
        store=store,
        obj_id=path_values.get("id"),
        query_values=query_values,
        limit=limit,
        offset=offset,
        start=start,
        body=kwargs.pop("request_body", None),
        list_path=list_path,
        list_key=_list_collection_key(list_path),
        use_background=(topology.supports_background and _affirmative(kwargs.get("background"))),
    )


def _get_list_response(request: _GeneratedRequest) -> dict[str, Any]:
    """Filter and paginate a generated collection response."""
    collection = request.store.get_collection(request.list_key)
    if collection is None:
        collection = _seed_list(
            request.topology.item_schema,
            request.resolver,
            collection_key=request.list_key,
        )
        request.store.replace_collection(request.list_key, collection)
    filtered = _filter_items(collection, request.query_values)
    if request.start is not None:
        return _paginate_results_cursor(
            filtered,
            start=request.start,
            limit=request.limit,
            base_url="http://mock.example.com",
            path=request.list_path,
        )
    return _paginate_results(
        filtered,
        limit=request.limit,
        offset=request.offset,
        base_url="http://mock.example.com",
        path=request.list_path,
    )


def _required_object_id(request: _GeneratedRequest) -> int:
    """Return the detail route ID or reject a missing value."""
    if request.obj_id is None:
        raise HTTPException(status_code=400, detail="Missing id parameter.")
    return request.obj_id


def _required_object_key(request: _GeneratedRequest) -> str:
    """Return the detail-store key or reject a missing route ID."""
    return _object_key(request.list_path, _required_object_id(request))


def _get_detail_response(request: _GeneratedRequest) -> Any:
    """Load or schema-seed one generated detail response."""
    obj_id = _required_object_id(request)
    if request.list_path == "/api/core/jobs/":
        job = request.store.poll_background_job(obj_id)
        if job is not None:
            return job
    obj_key = _required_object_key(request)
    if request.store.is_deleted(obj_key):
        raise HTTPException(status_code=404, detail="Not found.")
    obj = request.store.get_object(obj_key)
    if obj is None:
        obj = merge_with_schema_defaults(
            request.topology.item_schema or request.topology.response_schema,
            resolver=request.resolver,
            seed=obj_key,
        )
        if isinstance(obj, dict):
            obj = _enrich_created_object(
                obj,
                obj_id=obj_id,
                list_path=request.list_path,
            )
            obj = _normalize_response_object(
                obj,
                list_path=request.list_path,
                write_payload=None,
                store=request.store,
            )
        request.store.set_object(obj_key, obj)
    return obj


def _stub_response(request: _GeneratedRequest, *, seed: str) -> Any:
    """Build a deterministic response for non-CRUD action endpoints."""
    stub = sample_value_for_schema(
        request.topology.response_schema,
        resolver=request.resolver,
        seed=seed,
    )
    return stub if stub is not None else {}


def _get_response(request: _GeneratedRequest) -> Any:
    """Dispatch list, detail, and action GET behavior."""
    if request.topology.is_list:
        return _get_list_response(request)
    if request.topology.is_detail:
        return _get_detail_response(request)
    return _stub_response(request, seed=f"get_{request.topology.path_template}")


def _create_object(request: _GeneratedRequest, item_body: Any) -> dict[str, Any]:
    """Create, normalize, and store one object from a POST payload."""
    new_id = request.store.next_id(request.list_key)
    new_obj = merge_with_schema_defaults(
        request.topology.item_schema or request.topology.response_schema,
        resolver=request.resolver,
        seed=f"{request.list_key}_{new_id}",
        override=item_body if isinstance(item_body, dict) else None,
    )
    if not isinstance(new_obj, dict):
        new_obj = {}
    new_obj = _enrich_created_object(
        new_obj,
        obj_id=new_id,
        list_path=request.list_path,
    )
    new_obj["id"] = new_id
    new_obj = _normalize_response_object(
        new_obj,
        list_path=request.list_path,
        write_payload=item_body if isinstance(item_body, dict) else None,
        store=request.store,
    )
    obj_key = _object_key(request.list_path, new_id)
    request.store.set_object(obj_key, new_obj)
    request.store.upsert_collection_member(request.list_key, obj_key, new_obj)
    return new_obj


def _create_response(request: _GeneratedRequest) -> Any:
    """Validate and execute a singular or bulk collection POST."""
    is_bulk = isinstance(request.body, list)
    items = request.body if is_bulk else [request.body] if request.body is not None else [{}]
    if is_bulk:
        error_response = _bulk_error_response(
            _bulk_entry_errors(request, items, require_id=False),
            total=len(items),
            action="created",
        )
        if error_response is not None:
            return error_response
    else:
        errors = _entry_errors(request, items[0], bulk=False, require_id=False)
        for name, messages in _uniqueness_errors(request, items).get(0, {}).items():
            errors.setdefault(name, []).extend(messages)
        if errors:
            return JSONResponse(status_code=400, content=errors)
    created = [_create_object(request, item_body) for item_body in items]
    return created if is_bulk else created[0]


def _updated_value(
    request: _GeneratedRequest,
    *,
    existing: Any,
    body: dict[str, Any] | None,
    item_schema: dict[str, Any] | None,
    seed: str,
) -> Any:
    """Apply PUT replacement or PATCH merge semantics to an existing value."""
    if request.topology.method == "PUT":
        updated = merge_with_schema_defaults(
            item_schema,
            resolver=request.resolver,
            seed=seed,
            override=body,
        )
        return updated if isinstance(updated, dict) else {}
    updated = deepcopy(existing)
    return _deep_merge(updated, body) if body is not None else updated


def _update_detail_response(request: _GeneratedRequest) -> Any:
    """Execute one PUT or PATCH against a detail route."""
    obj_id = _required_object_id(request)
    obj_key = _required_object_key(request)
    if request.store.is_deleted(obj_key):
        raise HTTPException(status_code=404, detail="Not found.")
    existing = request.store.get_object(obj_key)
    existing = {} if existing is None else existing
    body = request.body if isinstance(request.body, dict) else None
    errors = _entry_errors(request, request.body, bulk=False, require_id=False)
    unique_item = dict(body or {})
    unique_item["id"] = obj_id
    for name, messages in _uniqueness_errors(request, [unique_item]).get(0, {}).items():
        errors.setdefault(name, []).extend(messages)
    if errors:
        return JSONResponse(status_code=400, content=errors)
    updated = _updated_value(
        request,
        existing=existing,
        body=body,
        item_schema=request.topology.item_schema or request.topology.response_schema,
        seed=obj_key,
    )
    if isinstance(updated, dict):
        updated["id"] = obj_id
        updated.setdefault("url", f"http://mock.example.com{obj_key}")
        updated.setdefault("display_url", f"http://mock.example.com{obj_key}")
        updated = _normalize_response_object(
            updated,
            list_path=request.list_path,
            write_payload=body,
            store=request.store,
        )
    request.store.set_object(obj_key, updated)
    request.store.upsert_collection_member(request.list_key, obj_key, updated)
    return updated


def _update_bulk_object(request: _GeneratedRequest, item_body: dict[str, Any]) -> dict[str, Any]:
    """Update, normalize, and store one already-validated bulk item."""
    item_id = item_body["id"]
    obj_key = _object_key(request.list_path, item_id)
    existing = request.store.get_object(obj_key) or {}
    updated = _updated_value(
        request,
        existing=existing,
        body=item_body,
        item_schema=request.topology.item_schema,
        seed=obj_key,
    )
    if not isinstance(updated, dict):
        updated = {}
    updated["id"] = int(item_id)
    updated = _normalize_response_object(
        updated,
        list_path=request.list_path,
        write_payload=item_body,
        store=request.store,
    )
    request.store.set_object(obj_key, updated)
    request.store.upsert_collection_member(request.list_key, obj_key, updated)
    return updated


def _bulk_update_response(request: _GeneratedRequest) -> Any:
    """Validate and execute a collection PUT or PATCH."""
    if not isinstance(request.body, list):
        raise HTTPException(status_code=400, detail="Bulk update requires a list.")
    bulk_errors = _bulk_entry_errors(request, request.body, require_id=True)
    error_response = _bulk_error_response(
        bulk_errors,
        total=len(request.body),
        action="updated",
    )
    if error_response is not None:
        return error_response
    return [
        _update_bulk_object(request, item_body)
        for item_body in request.body
        if isinstance(item_body, dict) and item_body.get("id") is not None
    ]


def _delete_detail_response(request: _GeneratedRequest) -> Response:
    """Delete one detail object and its collection member."""
    obj_key = _required_object_key(request)
    if request.store.is_deleted(obj_key):
        raise HTTPException(status_code=404, detail="Not found.")
    request.store.delete_collection_member(request.list_key, obj_key)
    request.store.delete_object(obj_key)
    return Response(status_code=204)


def _bulk_delete_response(request: _GeneratedRequest) -> Response | JSONResponse:
    """Validate and execute a collection DELETE."""
    if not isinstance(request.body, list):
        raise HTTPException(status_code=400, detail="Bulk delete requires a list.")
    bulk_errors = _bulk_entry_errors(request, request.body, require_id=True)
    error_response = _bulk_error_response(
        bulk_errors,
        total=len(request.body),
        action="deleted",
    )
    if error_response is not None:
        return error_response
    for item in request.body:
        obj_key = _object_key(request.list_path, item["id"])
        request.store.delete_collection_member(request.list_key, obj_key)
        request.store.delete_object(obj_key)
    return Response(status_code=204)


def _dispatch_generated_request(request: _GeneratedRequest) -> Any:
    """Dispatch parsed inputs to the route's cohesive CRUD behavior."""
    method = request.topology.method
    if request.use_background:
        return _background_job_response(request)
    if method == "GET":
        return _get_response(request)
    if method == "POST" and request.topology.is_list:
        return _create_response(request)
    if method in {"PUT", "PATCH"} and request.topology.is_detail:
        return _update_detail_response(request)
    if method in {"PUT", "PATCH"} and request.topology.is_list:
        return _bulk_update_response(request)
    if method == "DELETE" and request.topology.is_detail:
        return _delete_detail_response(request)
    if method == "DELETE" and request.topology.is_list:
        return _bulk_delete_response(request)
    return _stub_response(
        request,
        seed=f"{method.lower()}_{request.topology.path_template}",
    )


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
    path_params = _path_parameter_names(path_template)
    query_params, seen_params = _query_parameter_specs(topology, path_params)
    sig_params = _endpoint_signature_parameters(
        topology,
        path_params,
        query_params,
        seen_params,
    )

    async def generated_endpoint(**kwargs: Any) -> Any:
        request = _parse_generated_request(
            kwargs,
            topology=topology,
            resolver=resolver,
            schema_key=schema_key,
            namespace=namespace,
            path_params=path_params,
            query_params=query_params,
        )
        return _dispatch_generated_request(request)

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


def _seed_custom_mock_data(
    document_key: str,
    namespace: str | None,
    custom_mock_data: dict[str, Any] | None,
) -> None:
    """Populate initial collection and object state supplied by a mock caller."""
    if not custom_mock_data:
        return
    store = mock_store(document_key, namespace=namespace)
    for path_key, data in custom_mock_data.items():
        if isinstance(data, list):
            store.replace_collection(_list_collection_key(path_key), data)
        else:
            store.set_object(path_key, data)


def _item_schema_for_response(
    response_schema: dict[str, Any] | None,
    resolver: RefResolver,
) -> dict[str, Any] | None:
    """Resolve the object schema represented by a route response."""
    if not response_schema:
        return None
    kind = schema_kind(response_schema, resolver)
    if kind == "paginated_list":
        return extract_items_schema(response_schema, resolver)
    if kind not in {"object", "array"}:
        return None
    resolved = resolver.resolve(response_schema)
    return resolved if resolved.get("type") != "array" else resolved.get("items")


def _route_topology(
    *,
    path_template: str,
    method: str,
    operation: dict[str, Any],
    resolver: RefResolver,
    version: SupportedNetBoxVersion,
) -> NetBoxRouteTopology:
    """Build the complete schema-derived topology for one supported operation."""
    is_list, is_detail, is_action, group, resource = _classify_path(path_template)
    list_path = _list_path_for_detail(path_template) if is_detail or is_action else path_template
    request_schema = _extract_request_schema(operation)
    response_schema = _extract_response_schema(operation)
    return NetBoxRouteTopology(
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
        item_schema=_item_schema_for_response(response_schema, resolver),
        list_path_template=list_path if (is_detail or is_action) else None,
        supports_background=(
            version == "4.7"
            and is_list
            and method in {"POST", "PUT", "PATCH", "DELETE"}
            and _schema_allows_array(request_schema)
        ),
    )


def _iter_route_topologies(
    path_items: dict[str, dict[str, Any]],
    *,
    resolver: RefResolver,
    version: SupportedNetBoxVersion,
) -> Iterator[NetBoxRouteTopology]:
    """Yield supported, well-formed operations in deterministic route order."""
    for path_template, path_item in sorted(path_items.items()):
        for method_lower, operation in sorted(path_item.items()):
            method = method_lower.upper()
            if method not in _SUPPORTED_METHODS or not isinstance(operation, dict):
                continue
            yield _route_topology(
                path_template=path_template,
                method=method,
                operation=operation,
                resolver=resolver,
                version=version,
            )


def _register_topology(
    app: FastAPI | APIRouter,
    topology: NetBoxRouteTopology,
    *,
    resolver: RefResolver,
    schema_key: str,
    namespace: str | None,
) -> None:
    """Register one generated endpoint and its OpenAPI presentation metadata."""
    endpoint = _build_generated_endpoint(
        topology=topology,
        resolver=resolver,
        schema_key=schema_key,
        namespace=namespace,
    )
    operation = topology.operation
    route_name = (
        f"{_GENERATED_ROUTE_NAME_PREFIX}{topology.method.lower()}__"
        f"{_operation_id(topology.path_template, topology.method, operation)}"
    )
    kwargs: dict[str, Any] = {
        "path": topology.path_template,
        "endpoint": endpoint,
        "methods": [topology.method],
        "name": route_name,
        "summary": operation.get("summary"),
        "description": operation.get("description"),
        "tags": operation.get("tags", ["netbox mock"]),
        "status_code": _response_status(topology.method, topology.is_list),
    }
    if topology.method == "DELETE":
        kwargs["response_class"] = Response
        kwargs["response_model"] = None
    app.add_api_route(**kwargs)


def _publish_route_state(
    app: FastAPI | APIRouter,
    *,
    route_count: int,
    path_count: int,
    schema_version: Any,
) -> None:
    """Publish registration metadata and invalidate FastAPI's OpenAPI cache."""
    setattr(
        app,
        _ROUTE_STATE_ATTRIBUTE,
        {
            "route_count": route_count,
            "path_count": path_count,
            "method_count": route_count,
            "schema_version": schema_version,
        },
    )
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


def register_netbox_mock_routes(
    app: FastAPI | APIRouter,
    *,
    version: SupportedNetBoxVersion = DEFAULT_NETBOX_VERSION,
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
    _seed_custom_mock_data(doc_fingerprint, namespace, custom_mock_data)
    topologies = list(_iter_route_topologies(path_items, resolver=resolver, version=version))
    for topology in topologies:
        _register_topology(
            app,
            topology,
            resolver=resolver,
            schema_key=doc_fingerprint,
            namespace=namespace,
        )
    route_count = len(topologies)
    _publish_route_state(
        app,
        route_count=route_count,
        path_count=len(path_items),
        schema_version=schema_version,
    )
    return {
        "route_count": route_count,
        "path_count": len(path_items),
        "method_count": route_count,
        "schema_version": schema_version,
    }


def netbox_mock_route_state(app: FastAPI | APIRouter) -> dict[str, object]:
    """Return metadata owned by one mounted mock route set."""
    state = getattr(app, _ROUTE_STATE_ATTRIBUTE, None)
    if not isinstance(state, dict):
        raise RuntimeError("NetBox mock routes have not been registered on this app")
    return dict(state)


__all__ = [
    "NetBoxRouteTopology",
    "register_netbox_mock_routes",
    "netbox_mock_route_state",
]
