"""Stable JSON contracts for NetBox schema capability introspection."""

from __future__ import annotations

from typing import Any

from netbox_sdk.schema import FilterParam, Operation, SchemaIndex


def serialize_operation(operation: Operation) -> dict[str, str]:
    """Serialize one OpenAPI operation using the public capability contract."""
    return {
        "method": operation.method,
        "path": operation.path,
        "operation_id": operation.operation_id,
    }


def serialize_filter(filter_param: FilterParam) -> dict[str, Any]:
    """Serialize one filter parameter using JSON-compatible values."""
    return filter_param.model_dump(mode="json")


def serialize_groups(index: SchemaIndex) -> dict[str, list[str]]:
    """Return the stable group-list contract."""
    return {"groups": index.groups()}


def serialize_resources(index: SchemaIndex, group: str) -> dict[str, str | list[str]]:
    """Return the stable resource-list contract for ``group``."""
    return {"group": group, "resources": index.resources(group)}


def serialize_resource_description(
    index: SchemaIndex,
    group: str,
    resource: str,
) -> dict[str, Any]:
    """Return operations and filter parameters for one resource."""
    return {
        "group": group,
        "resource": resource,
        "operations": [
            serialize_operation(operation) for operation in index.operations_for(group, resource)
        ],
        "filters": [
            serialize_filter(filter_param) for filter_param in index.filter_params(group, resource)
        ],
    }


def serialize_capabilities(index: SchemaIndex) -> dict[str, Any]:
    """Return the complete nested schema capability document."""
    groups: dict[str, dict[str, Any]] = {}
    for group in index.groups():
        resources: dict[str, Any] = {}
        for resource in index.resources(group):
            description = serialize_resource_description(index, group, resource)
            resources[resource] = {
                "operations": description["operations"],
                "filters": description["filters"],
            }
        groups[group] = resources
    return {"groups": groups}
