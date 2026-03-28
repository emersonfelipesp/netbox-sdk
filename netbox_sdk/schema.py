"""OpenAPI schema parsing and resource indexing for dynamic NetBox commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from netbox_sdk.versioning import SupportedNetBoxVersion, bundled_openapi_path

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

# Query params that control pagination/format, not filters.
_FILTER_EXCLUDE_NAMES: frozenset[str] = frozenset({"limit", "offset", "format"})

# Lookup suffixes added by NetBox/django-filter — only the bare field name is shown.
_LOOKUP_SUFFIXES: tuple[str, ...] = (
    "__empty",
    "__gt",
    "__gte",
    "__ic",
    "__ie",
    "__iew",
    "__iregex",
    "__isw",
    "__lt",
    "__lte",
    "__n",
    "__nic",
    "__nie",
    "__niew",
    "__nisw",
    "__nre",
    "__nregex",
    "__re",
    "__regex",
)


class FilterParam(BaseModel):
    """A single query parameter available for filtering a list endpoint."""

    model_config = ConfigDict(frozen=True)

    name: str
    label: str
    type: str  # "string" | "integer" | "boolean" | "enum" | "array"
    choices: tuple[str, ...] = ()  # non-empty only when type == "enum"
    description: str = ""


class Operation(BaseModel):
    model_config = ConfigDict(frozen=True)

    group: str
    resource: str
    method: str
    path: str
    operation_id: str
    summary: str


class ResourcePaths(BaseModel):
    model_config = ConfigDict(frozen=True)

    list_path: str | None
    detail_path: str | None


def _classify_param(schema: dict[str, Any]) -> tuple[str, tuple[str, ...]]:
    if "enum" in schema:
        choices = tuple(str(v) for v in schema["enum"] if v is not None and str(v) != "null")
        return "enum", choices
    ptype = schema.get("type", "string")
    if ptype == "boolean":
        return "boolean", ()
    if ptype == "integer":
        return "integer", ()
    if ptype == "array":
        return "array", ()
    return "string", ()


class SchemaIndex:
    def __init__(self, schema: dict[str, Any]) -> None:
        self.schema = schema
        self.operations: list[Operation] = []
        self._resource_paths: dict[tuple[str, str], ResourcePaths] = {}
        self._build()

    def _build(self) -> None:
        resource_paths: dict[tuple[str, str], dict[str, str | None]] = {}
        paths = self.schema.get("paths")
        if not isinstance(paths, dict):
            return

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            group, resource = parse_group_resource(path)
            if group is None or resource is None:
                continue
            parts = [part for part in path.split("/") if part]

            key = (group, resource)
            if key not in resource_paths:
                resource_paths[key] = {"list_path": None, "detail_path": None}

            is_list = _is_list_path(parts, group, resource)
            is_detail = _is_detail_path(parts, group, resource)
            if is_list:
                resource_paths[key]["list_path"] = path
            if is_detail:
                resource_paths[key]["detail_path"] = path

            for method, operation in path_item.items():
                if method.lower() not in HTTP_METHODS:
                    continue
                if not isinstance(operation, dict):
                    continue
                self.operations.append(
                    Operation(
                        group=group,
                        resource=resource,
                        method=method.upper(),
                        path=path,
                        operation_id=str(operation.get("operationId") or ""),
                        summary=str(operation.get("summary") or ""),
                    )
                )

        self.operations.sort(key=lambda item: (item.group, item.resource, item.path, item.method))
        self._resource_paths = {
            key: ResourcePaths(list_path=val["list_path"], detail_path=val["detail_path"])
            for key, val in resource_paths.items()
        }

    def groups(self) -> list[str]:
        return sorted({item.group for item in self.operations})

    def resources(self, group: str) -> list[str]:
        return sorted({item.resource for item in self.operations if item.group == group})

    def operations_for(self, group: str, resource: str) -> list[Operation]:
        return [
            item for item in self.operations if item.group == group and item.resource == resource
        ]

    def resource_paths(self, group: str, resource: str) -> ResourcePaths | None:
        return self._resource_paths.get((group, resource))

    def filter_params(self, group: str, resource: str) -> list[FilterParam]:
        """Return filterable query parameters for GET /api/{group}/{resource}/ from the schema.

        Excludes lookup-suffix variants (``__ic``, ``__n``, etc.) and pagination
        params (``limit``, ``offset``, ``format``).  The result is sorted with
        ``q`` first, then alphabetically by name.
        """
        resource_paths = self.resource_paths(group, resource)
        list_path = resource_paths.list_path if resource_paths is not None else None
        if not list_path:
            return []
        paths = self.schema.get("paths", {})
        path_item = paths.get(list_path, {})
        if not isinstance(path_item, dict):
            return []
        get_op = path_item.get("get", {})
        if not isinstance(get_op, dict):
            return []
        parameters = get_op.get("parameters", [])
        if not isinstance(parameters, list):
            return []

        result: list[FilterParam] = []
        for param in parameters:
            if not isinstance(param, dict):
                continue
            if param.get("in") != "query":
                continue
            name = str(param.get("name", ""))
            if not name:
                continue
            if name in _FILTER_EXCLUDE_NAMES:
                continue
            if any(name.endswith(suffix) for suffix in _LOOKUP_SUFFIXES):
                continue

            schema = param.get("schema", {})
            if not isinstance(schema, dict):
                schema = {}
            ptype, choices = _classify_param(schema)
            label = name.replace("_", " ").replace("-", " ").title()
            description = str(param.get("description", ""))

            result.append(
                FilterParam(
                    name=name,
                    label=label,
                    type=ptype,
                    choices=choices,
                    description=description,
                )
            )

        # q first, then alphabetical
        result.sort(key=lambda p: (p.name != "q", p.name))
        return result

    def trace_path(self, group: str, resource: str) -> str | None:
        candidate = f"/api/{group}/{resource}/{{id}}/trace/"
        paths = self.schema.get("paths")
        if not isinstance(paths, dict):
            return candidate if group == "dcim" and resource == "cables" else None
        path_item = paths.get(candidate)
        if not isinstance(path_item, dict):
            return candidate if group == "dcim" and resource == "cables" else None
        if "get" not in {str(method).lower() for method in path_item.keys()}:
            return None
        return candidate

    def paths_path(self, group: str, resource: str) -> str | None:
        candidate = f"/api/{group}/{resource}/{{id}}/paths/"
        paths = self.schema.get("paths")
        if not isinstance(paths, dict):
            return None
        path_item = paths.get(candidate)
        if not isinstance(path_item, dict):
            return None
        if "get" not in {str(method).lower() for method in path_item.keys()}:
            return None
        return candidate

    def add_discovered_resource(
        self,
        *,
        group: str,
        resource: str,
        list_path: str,
        detail_path: str | None = None,
    ) -> bool:
        key = (group, resource)
        existing = self._resource_paths.get(key)
        current_list = existing.list_path if existing is not None else None
        current_detail = existing.detail_path if existing is not None else None
        if current_list == list_path and current_detail == detail_path:
            return False

        self._resource_paths[key] = ResourcePaths(list_path=list_path, detail_path=detail_path)

        existing_ops = {
            (op.method, op.path)
            for op in self.operations
            if op.group == group and op.resource == resource
        }
        synthetic: list[Operation] = []
        if ("GET", list_path) not in existing_ops:
            synthetic.append(
                Operation(
                    group=group,
                    resource=resource,
                    method="GET",
                    path=list_path,
                    operation_id=f"{group}_{resource.replace('/', '_')}_list_discovered",
                    summary="Discovered plugin list endpoint",
                )
            )
        if detail_path and ("GET", detail_path) not in existing_ops:
            synthetic.append(
                Operation(
                    group=group,
                    resource=resource,
                    method="GET",
                    path=detail_path,
                    operation_id=f"{group}_{resource.replace('/', '_')}_detail_discovered",
                    summary="Discovered plugin detail endpoint",
                )
            )
        if synthetic:
            self.operations.extend(synthetic)
            self.operations.sort(
                key=lambda item: (item.group, item.resource, item.path, item.method)
            )
        return True

    def remove_group_resources(self, group: str) -> bool:
        """Remove all resources and operations for a group from this mutable index."""
        original_count = len(self.operations)
        self.operations = [operation for operation in self.operations if operation.group != group]
        keys_to_remove = [key for key in self._resource_paths if key[0] == group]
        for key in keys_to_remove:
            self._resource_paths.pop(key, None)
        return len(self.operations) != original_count or bool(keys_to_remove)


def parse_group_resource(path: str) -> tuple[str | None, str | None]:
    parts = [part for part in path.split("/") if part]
    if len(parts) < 3 or parts[0] != "api":
        return None, None
    group = parts[1]
    if group == "plugins":
        if len(parts) < 4:
            return None, None
        resource = f"{parts[2]}/{parts[3]}"
        return group, resource
    resource = parts[2]
    return group, resource


def _resource_parts(group: str, resource: str) -> list[str]:
    if group == "plugins":
        return ["api", "plugins", *[part for part in resource.split("/") if part]]
    return ["api", group, resource]


def _is_list_path(parts: list[str], group: str, resource: str) -> bool:
    return parts == _resource_parts(group, resource)


def _is_detail_path(parts: list[str], group: str, resource: str) -> bool:
    return parts == [*_resource_parts(group, resource), "{id}"]


def load_openapi_schema(
    openapi_path: Path | None = None,
    *,
    version: SupportedNetBoxVersion | None = None,
) -> dict[str, Any]:
    if openapi_path is None:
        openapi_path = (
            bundled_openapi_path(version or "4.5")
            if version
            else (Path(__file__).resolve().parent / "reference" / "openapi" / "netbox-openapi.json")
        )
    text = openapi_path.read_text(encoding="utf-8")
    if openapi_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise RuntimeError("PyYAML is required to load YAML OpenAPI schemas") from exc
        loaded = yaml.safe_load(text)
    else:
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("OpenAPI schema must be a JSON/YAML object")
    return loaded


def build_schema_index(
    openapi_path: Path | None = None,
    *,
    version: SupportedNetBoxVersion | None = None,
) -> SchemaIndex:
    return SchemaIndex(load_openapi_schema(openapi_path, version=version))
