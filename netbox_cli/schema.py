from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


@dataclass(slots=True, frozen=True)
class Operation:
    group: str
    resource: str
    method: str
    path: str
    operation_id: str
    summary: str


@dataclass(slots=True, frozen=True)
class ResourcePaths:
    list_path: str | None
    detail_path: str | None


class SchemaIndex:
    def __init__(self, schema: dict[str, Any]):
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

            is_list = (
                len(parts) == 3
                and parts[0] == "api"
                and parts[1] == group
                and parts[2] == resource
            )
            is_detail = (
                len(parts) == 4
                and parts[0] == "api"
                and parts[1] == group
                and parts[2] == resource
                and parts[3] == "{id}"
            )
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

        self.operations.sort(
            key=lambda item: (item.group, item.resource, item.path, item.method)
        )
        self._resource_paths = {
            key: ResourcePaths(
                list_path=val["list_path"], detail_path=val["detail_path"]
            )
            for key, val in resource_paths.items()
        }

    def groups(self) -> list[str]:
        return sorted({item.group for item in self.operations})

    def resources(self, group: str) -> list[str]:
        return sorted(
            {item.resource for item in self.operations if item.group == group}
        )

    def operations_for(self, group: str, resource: str) -> list[Operation]:
        return [
            item
            for item in self.operations
            if item.group == group and item.resource == resource
        ]

    def resource_paths(self, group: str, resource: str) -> ResourcePaths | None:
        return self._resource_paths.get((group, resource))

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


def parse_group_resource(path: str) -> tuple[str | None, str | None]:
    parts = [part for part in path.split("/") if part]
    if len(parts) < 3 or parts[0] != "api":
        return None, None
    group = parts[1]
    resource = parts[2]
    return group, resource


def load_openapi_schema(openapi_path: Path | None = None) -> dict[str, Any]:
    if openapi_path is None:
        openapi_path = (
            Path(__file__).resolve().parents[1]
            / "reference"
            / "openapi"
            / "netbox-openapi.json"
        )
    text = openapi_path.read_text(encoding="utf-8")
    if openapi_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PyYAML is required to load YAML OpenAPI schemas"
            ) from exc
        loaded = yaml.safe_load(text)
    else:
        loaded = json.loads(text)
    if not isinstance(loaded, dict):
        raise ValueError("OpenAPI schema must be a JSON/YAML object")
    return loaded


def build_schema_index(openapi_path: Path | None = None) -> SchemaIndex:
    return SchemaIndex(load_openapi_schema(openapi_path))
