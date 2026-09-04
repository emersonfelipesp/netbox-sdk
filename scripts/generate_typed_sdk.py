"""Generate versioned Pydantic models and typed bindings from NetBox OpenAPI schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import os
import re
import shutil
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from netbox_sdk.versioning import release_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SDK_ROOT = REPO_ROOT / "netbox_sdk"
MODELS_ROOT = SDK_ROOT / "models"
TYPED_ROOT = SDK_ROOT / "typed_versions"
OPENAPI_ROOT = SDK_ROOT / "reference" / "openapi"
DATAMODEL_CODE_GENERATOR_VERSION = "0.55.0"
RUFF_VERSION = "0.15.9"
BYTE_FAITHFUL_RELEASE_BUNDLE_VERSIONS: frozenset[str] = frozenset({"4.7"})

RELEASE_PROVENANCE: dict[str, dict[str, str]] = {
    "4.7": {
        "netbox_release": "v4.7.0",
        "release_commit": "5f06007e4c9bacc93ce17c1e645fc1143d60df3d",
        "source_path": "contrib/openapi.json",
        "source_blob_sha": "ea7f7e9c38c37d2139c6600db584b249571524a6",
        "source_sha256": "be7f971179b1d6ba03b590c08ebe65966a32220ea8fdfd272f60dc5d66ea9008",
        "source_url": "https://github.com/netbox-community/netbox/blob/v4.7.0/contrib/openapi.json",
    },
    "4.6": {
        "netbox_release": "v4.6.6",
        "release_commit": "fb8c455ba61b57119a70670612dfdd05e8438b10",
        "source_path": "contrib/openapi.json",
        "source_blob_sha": "024d34500a04ec876fb3b32fa18c685e953a02f8",
        "source_sha256": "915a25d48e638ea49218f142af30271812f5f75f67ad619b05a9a9300c04f7d8",
        "source_url": "https://github.com/netbox-community/netbox/blob/v4.6.6/contrib/openapi.json",
    },
}

SCHEMA_SOURCES = {
    "4.7": Path("/tmp/netbox-v4.7.0-openapi.json"),
    "4.6": Path("/tmp/netbox-v4.6-openapi.json"),
    "4.5": Path("/tmp/netbox-v4.5.5/contrib/openapi.json"),
    "4.4": Path("/tmp/netbox-v4.4.10/contrib/openapi.json"),
    "4.3": Path("/tmp/go-netbox-v4.3.0/api/openapi.yaml"),
}

SPECIAL_METHOD_NAMES = {
    ("get", False, False): "list",
    ("post", False, False): "create",
    ("put", False, False): "bulk_update",
    ("patch", False, False): "bulk_partial_update",
    ("delete", False, False): "bulk_delete",
    ("get", True, False): "get",
    ("put", True, False): "update",
    ("patch", True, False): "partial_update",
    ("delete", True, False): "delete",
}


def snake_case(value: str) -> str:
    text = re.sub(r"[^0-9a-zA-Z]+", "_", value).strip("_").lower()
    if not text:
        text = "value"
    if text[0].isdigit():
        text = f"v_{text}"
    if keyword.iskeyword(text):
        text = f"{text}_"
    return text


def pascal_case(value: str) -> str:
    parts = [part for part in re.split(r"[^0-9a-zA-Z]+", value) if part]
    if not parts:
        return "Value"
    text = "".join(part[:1].upper() + part[1:] for part in parts)
    if text[:1].isdigit():
        text = f"V{text}"
    return text


def type_expr(schema: dict[str, Any] | None) -> str:
    if not schema:
        return "Any"
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if "oneOf" in schema:
        return " | ".join(type_expr(item) for item in schema["oneOf"])
    if "anyOf" in schema:
        return " | ".join(type_expr(item) for item in schema["anyOf"])
    if schema.get("type") == "array":
        return f"list[{type_expr(schema.get('items'))}]"
    if "enum" in schema:
        values = [repr(value) for value in schema["enum"] if value is not None]
        return "Literal[" + ", ".join(values) + "]" if values else "str"
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        members = [type_expr({"type": item}) for item in schema_type if item != "null"]
        expr = " | ".join(members) if members else "Any"
        if "null" in schema_type:
            expr = f"{expr} | None"
        return expr
    mapping: dict[str, str] = {
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "string": "str",
        "object": "dict[str, Any]",
    }
    if not isinstance(schema_type, str):
        return "Any"
    return mapping.get(schema_type, "Any")


@dataclass
class OperationSpec:
    method: str
    operation_id: str
    path: str
    method_name: str
    query_model_name: str | None
    body_model_expr: str | None
    body_media_type: str | None
    body_binary_field_names: tuple[str, ...]
    response_model_expr: str | None
    raw_response: bool = False
    path_param_names: tuple[str, ...] = ()
    background_query: bool = False
    accepts_bulk_create: bool = False


def render_query_model(name: str, parameters: list[dict[str, Any]]) -> str:
    lines = [f"class {name}(BaseModel):"]
    if not parameters:
        lines.append("    pass")
        return "\n".join(lines)
    for param in parameters:
        schema = param.get("schema") if isinstance(param, dict) else None
        field_name = snake_case(str(param.get("name", "value")))
        expr = type_expr(schema if isinstance(schema, dict) else None)
        required = bool(param.get("required"))
        if not required and "None" not in expr:
            expr = f"{expr} | None"
        alias = str(param.get("name", field_name))
        if field_name != alias:
            default = (
                f"Field(None, alias={alias!r})" if not required else f"Field(..., alias={alias!r})"
            )
        else:
            default = "..." if required else "None"
        lines.append(f"    {field_name}: {expr} = {default}")
    return "\n".join(lines)


def _resolve_schema_ref(
    schema: dict[str, Any],
    components: dict[str, Any],
    visited: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    ref = schema.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return schema
    if ref in visited:
        return {}
    resolved = components.get(ref.rsplit("/", 1)[-1])
    if not isinstance(resolved, dict):
        return {}
    return _resolve_schema_ref(resolved, components, visited | {ref})


def _schema_contains_binary(
    schema: dict[str, Any],
    components: dict[str, Any],
    visited: frozenset[str] = frozenset(),
) -> bool:
    if schema.get("format") == "binary":
        return True
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in visited:
            return False
        resolved = _resolve_schema_ref(schema, components, visited)
        return _schema_contains_binary(resolved, components, visited | {ref})
    for composition_keyword in ("oneOf", "anyOf", "allOf"):
        variants = schema.get(composition_keyword)
        if isinstance(variants, list) and any(
            _schema_contains_binary(item, components, visited)
            for item in variants
            if isinstance(item, dict)
        ):
            return True
    items = schema.get("items")
    if isinstance(items, dict) and _schema_contains_binary(items, components, visited):
        return True
    properties = schema.get("properties")
    return isinstance(properties, dict) and any(
        _schema_contains_binary(value, components, visited)
        for value in properties.values()
        if isinstance(value, dict)
    )


def _binary_field_names(
    schema: dict[str, Any],
    components: dict[str, Any],
    visited: frozenset[str] = frozenset(),
) -> tuple[str, ...]:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        if ref in visited:
            return ()
        resolved = _resolve_schema_ref(schema, components, visited)
        return _binary_field_names(resolved, components, visited | {ref})

    names: set[str] = set()
    properties = schema.get("properties")
    if isinstance(properties, dict):
        for name, value in properties.items():
            if isinstance(value, dict) and _schema_contains_binary(value, components, visited):
                names.add(str(name))
    for composition_keyword in ("oneOf", "anyOf", "allOf"):
        variants = schema.get(composition_keyword)
        if isinstance(variants, list):
            for variant in variants:
                if isinstance(variant, dict):
                    names.update(_binary_field_names(variant, components, visited))
    items = schema.get("items")
    if isinstance(items, dict):
        names.update(_binary_field_names(items, components, visited))
    return tuple(sorted(names))


@dataclass(frozen=True)
class RequestBodySpec:
    type_expr: str
    media_type: str
    binary_field_names: tuple[str, ...] = ()


def request_body_spec(
    operation: dict[str, Any], components: dict[str, Any]
) -> RequestBodySpec | None:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content")
    if not isinstance(content, dict):
        return None

    multipart = content.get("multipart/form-data")
    if isinstance(multipart, dict):
        multipart_schema = multipart.get("schema")
        if isinstance(multipart_schema, dict):
            binary_fields = _binary_field_names(multipart_schema, components)
            if binary_fields:
                return RequestBodySpec(
                    type_expr=type_expr(multipart_schema),
                    media_type="multipart/form-data",
                    binary_field_names=binary_fields,
                )

    for media_type in ("application/json", "multipart/form-data"):
        media = content.get(media_type)
        if isinstance(media, dict):
            schema = media.get("schema")
            if isinstance(schema, dict):
                return RequestBodySpec(
                    type_expr=type_expr(schema),
                    media_type=media_type,
                    binary_field_names=_binary_field_names(schema, components),
                )
    return None


def response_expr(operation: dict[str, Any]) -> tuple[str | None, bool]:
    responses = operation.get("responses")
    if not isinstance(responses, dict):
        return None, False
    for status in ("200", "201", "202"):
        response = responses.get(status)
        if not isinstance(response, dict):
            continue
        content = response.get("content")
        if not isinstance(content, dict):
            continue
        for media_type, media in content.items():
            if not isinstance(media, dict):
                continue
            schema = media.get("schema")
            if media_type == "application/json" and isinstance(schema, dict):
                return type_expr(schema), False
            if media_type != "application/json":
                return "str", True
    return None, False


def response_annotation(spec: OperationSpec) -> str:
    """Return the static response union for one generated operation."""
    response = spec.response_model_expr or "None"
    if spec.method_name == "get" and spec.response_model_expr is not None:
        response = f"{response} | None"
    if spec.accepts_bulk_create and spec.response_model_expr is not None:
        response = f"{response} | list[{spec.response_model_expr}]"
    if spec.background_query:
        if spec.response_model_expr is None:
            response = "BackgroundJobReference | None"
        else:
            response = f"{response} | BackgroundJobReference"
    return response


def path_param_names(path: str) -> tuple[str, ...]:
    return tuple(re.findall(r"{([^}]+)}", path))


def _api_path_parts(path: str) -> tuple[str, str, bool, str, str] | None:
    if not path.startswith("/api/"):
        return None
    parts = [part for part in path.split("/") if part]
    if len(parts) < 3:
        return None
    group = snake_case(parts[1])
    resource = snake_case(parts[2])
    is_detail = len(parts) >= 4 and parts[3].startswith("{") and parts[3].endswith("}")
    action_parts = parts[4:] if is_detail else parts[3:]
    action_name = snake_case("_".join(action_parts)) if action_parts else ""
    query_scope = action_name or ("detail" if is_detail else "root")
    return group, resource, is_detail, action_name, query_scope


def _operation_method_name(
    method: str,
    operation: dict[str, Any],
    *,
    is_detail: bool,
    action_name: str,
) -> str:
    is_action = bool(action_name)
    if is_action:
        action_method = {
            "get": "list",
            "post": "create",
            "put": "update",
            "patch": "partial_update",
            "delete": "delete",
        }.get(method)
        if action_method is not None:
            return action_method
    special_method = SPECIAL_METHOD_NAMES.get((method, is_detail, is_action))
    if special_method is not None:
        return special_method
    return snake_case(operation.get("operationId") or f"{method}_{action_name or 'call'}")


def _register_query_model(
    query_models: dict[str, str],
    *,
    class_key: str,
    method: str,
    path: str,
    params: list[dict[str, Any]],
) -> str | None:
    if not params:
        return None
    query_model_name = f"{class_key}{pascal_case(method)}Query"
    rendered_query = render_query_model(query_model_name, params)
    existing_query = query_models.get(query_model_name)
    if existing_query is not None and existing_query != rendered_query:
        raise ValueError(
            f"Conflicting query model {query_model_name!r} generated for {method.upper()} {path}"
        )
    query_models[query_model_name] = rendered_query
    return query_model_name


def _build_operation_spec(
    version: str,
    operation: dict[str, Any],
    components: dict[str, Any],
    *,
    method: str,
    path: str,
    method_name: str,
    query_model_name: str | None,
    params: list[dict[str, Any]],
) -> OperationSpec:
    body_spec = request_body_spec(operation, components)
    response_model_expr, raw_response = response_expr(operation)
    accepts_bulk_create = (
        version == "4.7"
        and method_name == "create"
        and body_spec is not None
        and "list[" in body_spec.type_expr
    )
    return OperationSpec(
        method=method.upper(),
        operation_id=str(operation.get("operationId") or ""),
        path=path,
        method_name=method_name,
        query_model_name=query_model_name,
        body_model_expr=body_spec.type_expr if body_spec else None,
        body_media_type=body_spec.media_type if body_spec else None,
        body_binary_field_names=body_spec.binary_field_names if body_spec else (),
        response_model_expr=response_model_expr,
        raw_response=raw_response,
        path_param_names=path_param_names(path),
        background_query=any(param.get("name") == "background" for param in params),
        accepts_bulk_create=accepts_bulk_create,
    )


def _collect_operations(
    version: str,
    schema: dict[str, Any],
) -> tuple[dict[str, dict[str, list[OperationSpec]]], dict[str, str]]:
    per_group_resources: dict[str, dict[str, list[OperationSpec]]] = defaultdict(
        lambda: defaultdict(list)
    )
    query_models: dict[str, str] = {}
    components = schema.get("components", {}).get("schemas", {})
    if not isinstance(components, dict):
        components = {}

    for path, path_item in schema.get("paths", {}).items():
        path_parts = _api_path_parts(path)
        if not isinstance(path_item, dict) or path_parts is None:
            continue
        group, resource, is_detail, action_name, query_scope = path_parts
        class_key = pascal_case(f"{group}_{resource}_{query_scope}")

        for method, operation in path_item.items():
            normalized_method = method.lower()
            if normalized_method not in {"get", "post", "put", "patch", "delete"} or not isinstance(
                operation, dict
            ):
                continue
            params = [
                param
                for param in operation.get("parameters", [])
                if isinstance(param, dict) and param.get("in") == "query"
            ]
            query_model_name = _register_query_model(
                query_models,
                class_key=class_key,
                method=normalized_method,
                path=path,
                params=params,
            )
            method_name = _operation_method_name(
                normalized_method,
                operation,
                is_detail=is_detail,
                action_name=action_name,
            )
            spec = _build_operation_spec(
                version,
                operation,
                components,
                method=normalized_method,
                path=path,
                method_name=method_name,
                query_model_name=query_model_name,
                params=params,
            )
            resource_key = resource if not action_name else f"{resource}:{action_name}"
            per_group_resources[group][resource_key].append(spec)
    return per_group_resources, query_models


def _runtime_imports(
    per_group_resources: dict[str, dict[str, list[OperationSpec]]],
) -> tuple[list[str], bool]:
    raw_plugin_fallback = "plugins" not in per_group_resources
    specs = (
        spec
        for resources in per_group_resources.values()
        for operations in resources.values()
        for spec in operations
    )
    has_background_operation = any(spec.background_query for spec in specs)
    imports = ["TypedApiBase", "TypedAppBase", "build_typed_client"]
    if has_background_operation:
        imports.append("BackgroundJobReference")
    if raw_plugin_fallback:
        imports.insert(0, "RawBranchingApp")
    return imports, raw_plugin_fallback


def _binding_import_lines(version: str, runtime_imports: list[str]) -> list[str]:
    suffix = version.replace(".", "_")
    return [
        '"""',
        f"Auto-generated typed NetBox {version} API bindings from OpenAPI.",
        "",
        "Do not edit by hand. Regenerate with scripts/generate_typed_sdk.py.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Literal",
        "",
        "from pydantic import BaseModel, Field",
        "",
        "from netbox_sdk.client import NetBoxApiClient",
        f"from netbox_sdk.models.v{suffix} import *  # noqa: F403, F405",
        f"from netbox_sdk.typed_runtime import {', '.join(runtime_imports)}",
        "",
    ]


def _query_model_lines(query_models: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for model_name in sorted(query_models):
        lines.extend((query_models[model_name], ""))
    return lines


def _child_resource_map(resource_keys: dict[str, list[OperationSpec]]) -> dict[str, list[str]]:
    child_map: dict[str, list[str]] = defaultdict(list)
    for key in resource_keys:
        if ":" in key:
            parent, child = key.split(":", 1)
            child_map[parent].append(child)
    return child_map


def _operation_signature(spec: OperationSpec) -> tuple[str, str]:
    path_params: list[str] = []
    path_expr = spec.path
    for name in spec.path_param_names:
        py_name = snake_case(name)
        path_params.append(f"{py_name}: int | str")
        path_expr = path_expr.replace(f"{{{name}}}", f"{{{py_name}}}")
    params = ["self", *path_params]
    if spec.body_model_expr is not None:
        body_annotation = spec.body_model_expr
        if spec.body_media_type == "multipart/form-data":
            body_annotation = f"{body_annotation} | dict[str, Any]"
        params.append(f"body: {body_annotation}")
    if spec.query_model_name is not None:
        params.append(f"query: {spec.query_model_name} | dict[str, Any] | None = None")
    return ", ".join(params), path_expr


def _typed_request_line(spec: OperationSpec) -> str:
    if spec.raw_response:
        query_arg = "query=query" if spec.query_model_name is not None else "query=None"
        query_model = spec.query_model_name or "None"
        return (
            f"        return await self._typed_raw_request({spec.method!r}, path, "
            f"query_model={query_model}, {query_arg})"
        )
    kwargs = [
        f"query_model={spec.query_model_name or 'None'}",
        f"query={'query' if spec.query_model_name is not None else 'None'}",
        f"body_model={spec.body_model_expr or 'None'}",
        f"body={'body' if spec.body_model_expr is not None else 'None'}",
        f"response_model={spec.response_model_expr or 'None'}",
        f"return_none_on_404={'True' if spec.method_name == 'get' else 'False'}",
    ]
    request_method = "_typed_json_request"
    if spec.body_media_type == "multipart/form-data":
        request_method = "_typed_multipart_request"
        kwargs.append(f"binary_field_names={spec.body_binary_field_names!r}")
    return f"        return await self.{request_method}({spec.method!r}, path, {', '.join(kwargs)})"


def _operation_lines(spec: OperationSpec) -> list[str]:
    signature, path_expr = _operation_signature(spec)
    lines = [f"    async def {spec.method_name}({signature}) -> {response_annotation(spec)}:"]
    path_literal = f'f"{path_expr}"' if spec.path_param_names else f'"{path_expr}"'
    lines.extend((f"        path = {path_literal}", _typed_request_line(spec), ""))
    return lines


def _endpoint_class(
    version: str,
    group: str,
    resource_key: str,
    operations: list[OperationSpec],
    child_map: dict[str, list[str]],
) -> str:
    resource_name, _, action_name = resource_key.partition(":")
    class_name = pascal_case(f"{group}_{resource_name}_{action_name or 'endpoint'}")
    lines = [
        f"class {class_name}(TypedAppBase):",
        f'    """Typed OpenAPI resource `{group}/{resource_key}` for NetBox {version}."""',
        "    def __init__(self, api: TypedApiBase) -> None:",
        "        super().__init__(api)",
        "",
    ]
    if not action_name:
        for child in sorted(child_map.get(resource_name, [])):
            child_class = pascal_case(f"{group}_{resource_name}_{child}")
            attr_name = snake_case(child)
            lines.extend(
                (
                    "    @property",
                    f"    def {attr_name}(self) -> {child_class}:",
                    f"        return {child_class}(self._api)",
                    "",
                )
            )
    for spec in operations:
        lines.extend(_operation_lines(spec))
    if len(lines) == 5:
        lines.extend(("    pass", ""))
    return "\n".join(lines)


def _group_app_class(version: str, group: str, root_resources: list[str]) -> str:
    app_class_name = pascal_case(f"{group}_app")
    lines = [
        f"class {app_class_name}(TypedAppBase):",
        f'    """Typed API group `{group}` for NetBox {version}."""',
        "    def __init__(self, api: TypedApiBase) -> None:",
        "        super().__init__(api)",
        "",
    ]
    for resource in root_resources:
        endpoint_class = pascal_case(f"{group}_{resource}_endpoint")
        lines.extend(
            (
                "    @property",
                f"    def {resource}(self) -> {endpoint_class}:",
                f"        return {endpoint_class}(self._api)",
                "",
            )
        )
    if len(lines) == 5:
        lines.extend(("    pass", ""))
    return "\n".join(lines)


def _render_group(
    version: str,
    group: str,
    resources: dict[str, list[OperationSpec]],
) -> tuple[list[str], str, str]:
    root_resources = sorted(key for key in resources if ":" not in key)
    child_map = _child_resource_map(resources)
    endpoint_classes: list[str] = []
    for resource_key, operations in sorted(resources.items()):
        endpoint_classes.extend(
            (_endpoint_class(version, group, resource_key, operations, child_map), "")
        )
    app_class_name = pascal_case(f"{group}_app")
    app_class = _group_app_class(version, group, root_resources)
    assignment = f"        self.{group} = {app_class_name}(self)"
    return endpoint_classes, app_class, assignment


def _plugin_fallback_class() -> str:
    return "\n".join(
        [
            "class PluginsApp(TypedAppBase):",
            '    """Typed-client access to NetBox plugin endpoints."""',
            "    def __init__(self, api: TypedApiBase) -> None:",
            "        super().__init__(api)",
            "",
            "    @property",
            "    def branching(self) -> RawBranchingApp:",
            "        return RawBranchingApp(self._api)",
            "",
        ]
    )


def _root_api_lines(version: str, api_assignments: list[str]) -> tuple[list[str], list[str]]:
    suffix = version.replace(".", "_")
    api_class_name = f"TypedApiV{suffix}"
    api_lines = [
        f"class {api_class_name}(TypedApiBase):",
        f'    """Root typed client for NetBox release line {version!r}."""',
        "    def __init__(self, client: NetBoxApiClient) -> None:",
        f"        super().__init__(client=client, netbox_version={version!r})",
        *api_assignments,
        "",
    ]
    factory_lines = [
        f"def build_api(url: str, token: str | None = None) -> {api_class_name}:",
        f'    """Build :class:`{api_class_name}` using the shared typed HTTP client."""',
        "    client = build_typed_client(url, token)",
        f"    return {api_class_name}(client)",
        "",
    ]
    return api_lines, factory_lines


def build_bindings(version: str, schema: dict[str, Any]) -> str:
    per_group_resources, query_models = _collect_operations(version, schema)
    runtime_imports, raw_plugin_fallback = _runtime_imports(per_group_resources)
    imports = _binding_import_lines(version, runtime_imports)
    body = _query_model_lines(query_models)

    endpoint_classes: list[str] = []
    app_classes: list[str] = []
    api_assignments: list[str] = []
    for group in sorted(per_group_resources):
        group_endpoints, group_app, assignment = _render_group(
            version, group, per_group_resources[group]
        )
        endpoint_classes.extend(group_endpoints)
        app_classes.extend((group_app, ""))
        api_assignments.append(assignment)

    if raw_plugin_fallback:
        app_classes.extend((_plugin_fallback_class(), ""))
        api_assignments.append("        self.plugins = PluginsApp(self)")

    api_lines, factory_lines = _root_api_lines(version, api_assignments)
    return "\n".join(imports + body + endpoint_classes + app_classes + api_lines + factory_lines)


# Background bulk-operation overlay
# ---------------------------------------------------------------------------
# NetBox 4.7 adds ``?background=true`` to bulk POST/PUT/PATCH/DELETE on collection
# paths, answering 202 with a job reference instead of executing synchronously.
# It exists specifically to avoid proxy timeouts on large batches.
#
# The pinned upstream artifact is ``v4.7.0``, whose OpenAPI document does not
# describe the capability at all (0 ``background`` parameters, 0 ``202``
# responses -- asserted by a guard test). The generated bindings are therefore
# *faithful to the artifact*, and the typed surface simply cannot reach a feature
# the raw client can already use.
#
# Remove this the moment an upstream schema describes the parameter; the guard
# test in tests/test_typed_background_bulk.py fails if the overlay outlives its
# reason to exist. The release registry is shared with the mock server so its
# capability surface cannot drift from the generated bindings.
BACKGROUND_BULK_OVERLAY_VERSIONS: frozenset[str] = frozenset(
    record.line for record in release_lines() if record.background_bulk_overlay
)

_BACKGROUND_PARAMETER: dict[str, Any] = {
    "in": "query",
    "name": "background",
    "schema": {"type": "boolean"},
    "description": (
        "Execute this bulk operation as a background job. The response is 202 with a "
        "job reference instead of the committed objects."
    ),
}

_BACKGROUND_METHODS = ("post", "put", "patch", "delete")


def _is_collection_path(path: str) -> bool:
    """True for a collection path -- no ``{...}`` placeholder.

    Necessary but not sufficient for a bulk write. Singular resources such as
    the extras dashboard also live at parameter-free paths.
    """
    return path.startswith("/api/") and "{" not in path


def _deref_local_schema(schema_doc: dict[str, Any], node: Any) -> Any:
    """Follow one local ``#/components/schemas/`` pointer, otherwise return ``node``."""
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return node
    name = ref.rsplit("/", 1)[-1]
    components = schema_doc.get("components")
    schemas = components.get("schemas") if isinstance(components, dict) else None
    if not isinstance(schemas, dict):
        return node
    target = schemas.get(name)
    return target if isinstance(target, dict) else node


def _json_body_schema(operation: dict[str, Any]) -> Any:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content")
    if not isinstance(content, dict):
        return None
    json_content = content.get("application/json")
    if not isinstance(json_content, dict):
        return None
    return json_content.get("schema")


def _schema_node_is_array(schema_doc: dict[str, Any], node: Any) -> bool:
    """True when ``node`` is an array schema or a oneOf/anyOf that includes one."""
    resolved = _deref_local_schema(schema_doc, node)
    if not isinstance(resolved, dict):
        return False
    if resolved.get("type") == "array":
        return True
    for key in ("oneOf", "anyOf"):
        variants = resolved.get(key)
        if isinstance(variants, list) and any(
            _schema_node_is_array(schema_doc, variant) for variant in variants
        ):
            return True
    return False


def _is_bulk_write_operation(
    schema_doc: dict[str, Any], path: str, operation: dict[str, Any]
) -> bool:
    """True when the operation accepts a JSON array (NetBox bulk create/update/delete)."""
    return _is_collection_path(path) and _schema_node_is_array(
        schema_doc, _json_body_schema(operation)
    )


def apply_background_bulk_overlay(version: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``schema`` declaring ``?background=true`` on bulk writes.

    Eligibility is the JSON request body, not the path shape. Parameter-free
    paths such as ``/api/extras/dashboard/`` and ``/api/extras/scripts/upload/``
    are singular mutations; advertising ``background`` there would make the
    runtime expect ``BackgroundJobReference`` after a write that already
    committed.

    Applied to an in-memory copy only; the committed ``netbox-openapi-*.json``
    stays byte-faithful to the pinned upstream artifact, so provenance
    verification is unaffected.
    """
    if version not in BACKGROUND_BULK_OVERLAY_VERSIONS:
        return schema
    patched = json.loads(json.dumps(schema))
    paths = patched.get("paths")
    if not isinstance(paths, dict):
        return patched
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method in _BACKGROUND_METHODS:
            operation = item.get(method)
            if not isinstance(operation, dict):
                continue
            if not _is_bulk_write_operation(patched, path, operation):
                continue
            parameters = operation.setdefault("parameters", [])
            if not isinstance(parameters, list):
                continue
            if any(
                isinstance(p, dict) and p.get("name") == "background" and p.get("in") == "query"
                for p in parameters
            ):
                continue  # upstream now describes it; nothing to add
            parameters.append(json.loads(json.dumps(_BACKGROUND_PARAMETER)))
    return patched


def _datamodel_codegen_command() -> list[str]:
    executable = shutil.which("datamodel-codegen")
    if executable is None:
        raise RuntimeError(
            "datamodel-codegen is not on PATH; install the locked development extra "
            f"(uv sync --dev) so generation uses datamodel-code-generator=="
            f"{DATAMODEL_CODE_GENERATOR_VERSION}"
        )
    return [executable]


def generate_models(version: str, input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")
    env.setdefault("UV_TOOL_DIR", "/tmp/uv-tools")
    subprocess.run(
        [
            *_datamodel_codegen_command(),
            "--input",
            str(input_path),
            "--input-file-type",
            "openapi",
            "--output",
            str(output_path),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.11",
            "--use-title-as-name",
            "--reuse-model",
            "--enum-field-as-literal",
            "all",
            "--disable-timestamp",
        ],
        check=True,
        env=env,
    )


def _ruff_command() -> list[str]:
    executable = shutil.which("ruff")
    if executable is None:
        return ["uvx", "--from", f"ruff=={RUFF_VERSION}", "ruff"]

    result = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != f"ruff {RUFF_VERSION}":
        raise RuntimeError(
            f"Expected ruff {RUFF_VERSION}, found {result.stdout.strip() or 'unknown'}"
        )
    return [executable]


def format_generated_artifacts(paths: list[Path]) -> None:
    """Format generated Python artifacts with the pinned Ruff release."""

    if not paths:
        return
    env = dict(os.environ)
    env.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")
    env.setdefault("UV_TOOL_DIR", "/tmp/uv-tools")
    subprocess.run(
        [*_ruff_command(), "format", *(str(path) for path in paths)],
        check=True,
        env=env,
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_output(repository: Path, *args: str, text: bool = True) -> str | bytes:
    """Run one read-only Git query against an upstream checkout."""
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=True,
        capture_output=True,
        text=text,
    )
    return result.stdout.strip() if text else result.stdout


def _release_source_blob(repository: Path, commit: str, source_path: str) -> str:
    """Resolve one source path with ``git ls-tree`` without revision-path syntax."""
    raw = _git_output(
        repository,
        "ls-tree",
        "-z",
        commit,
        "--",
        source_path,
        text=False,
    )
    if not isinstance(raw, bytes):
        raise ValueError("git ls-tree returned text instead of bytes")
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1:
        raise ValueError(
            f"Expected exactly one Git tree entry for {source_path!r}, found {len(entries)}"
        )
    try:
        metadata, recorded_path = entries[0].split(b"\t", 1)
        _mode, object_type, object_id = metadata.decode("ascii").split()
        decoded_path = recorded_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"Malformed Git tree entry for {source_path!r}") from exc
    if object_type != "blob" or decoded_path != source_path:
        raise ValueError(f"Git tree entry for {source_path!r} is not the expected blob path")
    return object_id


def _validate_release_git_objects(
    version: str,
    source_path: Path,
    release_repository: Path,
) -> None:
    """Bind a pinned source file to its reviewed tag, commit, path, and blob."""
    release = RELEASE_PROVENANCE[version]
    tag_ref = f"refs/tags/{release['netbox_release']}^{{commit}}"
    try:
        tag_commit = _git_output(release_repository, "rev-parse", "--verify", tag_ref)
        commit_type = _git_output(
            release_repository,
            "cat-file",
            "-t",
            release["release_commit"],
        )
        source_blob = _release_source_blob(
            release_repository,
            release["release_commit"],
            release["source_path"],
        )
        blob_bytes = _git_output(
            release_repository,
            "cat-file",
            "blob",
            release["source_blob_sha"],
            text=False,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            f"Cannot verify immutable NetBox {release['netbox_release']} Git provenance "
            f"in {release_repository}"
        ) from exc

    if tag_commit != release["release_commit"]:
        raise ValueError(
            f"NetBox {release['netbox_release']} tag target mismatch: expected "
            f"{release['release_commit']}, got {tag_commit}"
        )
    if commit_type != "commit":
        raise ValueError(
            f"NetBox {release['netbox_release']} release object is not a commit: {commit_type}"
        )
    if source_blob != release["source_blob_sha"]:
        raise ValueError(
            f"NetBox {release['netbox_release']} source blob mismatch: expected "
            f"{release['source_blob_sha']}, got {source_blob}"
        )
    blob_digest = hashlib.sha256(blob_bytes).hexdigest()
    if blob_digest != release["source_sha256"]:
        raise ValueError(
            f"NetBox {release['netbox_release']} Git blob SHA-256 mismatch: expected "
            f"{release['source_sha256']}, got {blob_digest}"
        )
    if blob_bytes != source_path.read_bytes():
        raise ValueError(
            f"NetBox {release['netbox_release']} source bytes do not match Git blob "
            f"{release['source_blob_sha']}"
        )


def validate_release_source(
    version: str,
    source_path: Path,
    *,
    release_repository: Path | None = None,
) -> None:
    """Reject release inputs that do not match the pinned artifact and Git objects."""

    release = RELEASE_PROVENANCE.get(version)
    if release is None:
        return
    expected = release["source_sha256"]
    actual = _sha256(source_path)
    if actual != expected:
        raise ValueError(
            f"NetBox {release['netbox_release']} source SHA-256 mismatch for "
            f"{source_path}: expected {expected}, got {actual}"
        )
    if release_repository is None:
        raise ValueError(
            f"NetBox {release['netbox_release']} requires an upstream Git checkout "
            "to verify its immutable tag, commit, and source blob"
        )
    _validate_release_git_objects(version, source_path, release_repository)


def validate_release_bundle(version: str, source_path: Path, bundled_path: Path) -> None:
    """Require the committed bundle to satisfy its reviewed source-byte contract."""
    if version in BYTE_FAITHFUL_RELEASE_BUNDLE_VERSIONS:
        if source_path.read_bytes() != bundled_path.read_bytes():
            raise ValueError(
                f"Bundled schema {bundled_path} is not byte-for-byte identical to "
                f"reviewed upstream source {source_path}"
            )
        return

    source = load_schema(source_path)
    bundled = load_schema(bundled_path)
    if source != bundled:
        raise ValueError(
            f"Bundled schema {bundled_path} does not match normalized source {source_path}"
        )


def _release_artifact_paths(version: str, bundled_path: Path) -> dict[str, Path]:
    suffix = version.replace(".", "_")
    return {
        bundled_path.name: bundled_path,
        f"models/v{suffix}.py": MODELS_ROOT / f"v{suffix}.py",
        f"typed_versions/v{suffix}.py": TYPED_ROOT / f"v{suffix}.py",
    }


def _load_release_provenance(bundled_path: Path) -> dict[str, Any]:
    provenance_path = bundled_path.with_name(f"{bundled_path.stem}.provenance.json")
    if not provenance_path.is_file():
        raise FileNotFoundError(f"Release provenance not found: {provenance_path}")
    try:
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Release provenance is not valid JSON: {provenance_path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Release provenance must be a JSON object: {provenance_path}")
    return payload


def _validate_release_provenance_metadata(version: str, payload: dict[str, Any]) -> None:
    """Anchor documentary provenance to reviewed constants outside the sidecar."""
    release = RELEASE_PROVENANCE.get(version)
    if release is None:
        raise ValueError(f"NetBox {version} has no immutable release provenance contract")
    expected: dict[str, Any] = {
        **release,
        "generator": {
            "name": "datamodel-code-generator",
            "version": DATAMODEL_CODE_GENERATOR_VERSION,
            "timestamp_disabled": True,
        },
        "formatter": {"name": "ruff", "version": RUFF_VERSION},
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            raise ValueError(
                f"Release provenance {field} mismatch for NetBox {version}: "
                f"expected {value!r}, got {payload.get(field)!r}"
            )


def _validate_recorded_artifact_hashes(
    version: str,
    payload: dict[str, Any],
    expected: dict[str, Path],
) -> None:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(expected):
        raise ValueError(
            f"Release provenance artifact set mismatch for NetBox {version}: "
            f"expected {sorted(expected)}, got {sorted(artifacts) if isinstance(artifacts, dict) else artifacts}"
        )
    for name, path in expected.items():
        if not path.is_file():
            raise FileNotFoundError(f"Release artifact not found: {path}")
        actual = _sha256(path)
        if artifacts[name] != actual:
            raise ValueError(
                f"Release artifact hash mismatch for {name}: expected {artifacts[name]}, got {actual}"
            )


def _regenerate_release_artifacts(
    version: str,
    bundled_path: Path,
    output_root: Path,
) -> dict[str, Path]:
    """Regenerate deterministic Python artifacts from the committed schema."""
    suffix = version.replace(".", "_")
    model_output = output_root / f"models-v{suffix}.py"
    typed_output = output_root / f"typed-v{suffix}.py"
    generate_models(version, bundled_path, model_output)
    _prepend_models_module_doc(model_output, version)
    schema = load_schema(bundled_path)
    typed_output.write_text(
        build_bindings(version, apply_background_bulk_overlay(version, schema)),
        encoding="utf-8",
    )
    format_generated_artifacts([model_output, typed_output])
    return {
        f"models/v{suffix}.py": model_output,
        f"typed_versions/v{suffix}.py": typed_output,
    }


def validate_release_artifact_hashes(version: str, bundled_path: Path) -> None:
    """Verify provenance metadata, recorded hashes, and deterministic regeneration."""
    if version in BYTE_FAITHFUL_RELEASE_BUNDLE_VERSIONS:
        reviewed_digest = RELEASE_PROVENANCE[version]["source_sha256"]
        bundled_digest = _sha256(bundled_path)
        if bundled_digest != reviewed_digest:
            raise ValueError(
                f"Bundled schema {bundled_path} does not match reviewed upstream bytes: "
                f"expected SHA-256 {reviewed_digest}, got {bundled_digest}"
            )

    payload = _load_release_provenance(bundled_path)
    expected = _release_artifact_paths(version, bundled_path)
    _validate_release_provenance_metadata(version, payload)
    _validate_recorded_artifact_hashes(version, payload, expected)

    with TemporaryDirectory(prefix=f"netbox-sdk-v{version.replace('.', '-')}-verify-") as temp_dir:
        regenerated = _regenerate_release_artifacts(version, bundled_path, Path(temp_dir))
        for name, generated_path in regenerated.items():
            committed_path = expected[name]
            if generated_path.read_bytes() != committed_path.read_bytes():
                raise ValueError(
                    f"Release artifact deterministic regeneration mismatch for {name}: "
                    f"{committed_path} was not generated from {bundled_path}"
                )


def write_release_provenance(
    version: str,
    *,
    source_path: Path,
    release_repository: Path,
    bundled_path: Path,
    model_path: Path,
    typed_path: Path,
) -> Path | None:
    """Write immutable source, tool, and artifact hashes for a release line."""

    release = RELEASE_PROVENANCE.get(version)
    if release is None:
        return None
    missing = [
        str(path)
        for path in (source_path, bundled_path, model_path, typed_path)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(f"Cannot write provenance; missing artifacts: {missing}")
    validate_release_source(
        version,
        source_path,
        release_repository=release_repository,
    )
    validate_release_bundle(version, source_path, bundled_path)

    payload: dict[str, Any] = {
        **release,
        "generator": {
            "name": "datamodel-code-generator",
            "version": DATAMODEL_CODE_GENERATOR_VERSION,
            "timestamp_disabled": True,
        },
        "formatter": {"name": "ruff", "version": RUFF_VERSION},
        "artifacts": {
            bundled_path.name: _sha256(bundled_path),
            f"models/{model_path.name}": _sha256(model_path),
            f"typed_versions/{typed_path.name}": _sha256(typed_path),
        },
    }
    output_path = bundled_path.with_name(f"{bundled_path.stem}.provenance.json")
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output_path


def _prepend_models_module_doc(output_path: Path, version: str) -> None:
    """Insert a module docstring after datamodel-codegen banner comments."""
    text = output_path.read_text(encoding="utf-8")
    if "Pydantic models generated from NetBox" in text[:800]:
        return
    lines = text.splitlines(keepends=True)
    i = 0
    while i < len(lines) and (lines[i].startswith("#") or lines[i].strip() == ""):
        i += 1
    doc = (
        '"""\n'
        f"Pydantic models generated from NetBox {version} OpenAPI.\n\n"
        "Do not edit by hand. Regenerate with scripts/generate_typed_sdk.py.\n"
        '"""\n\n'
    )
    output_path.write_text("".join(lines[:i]) + doc + "".join(lines[i:]), encoding="utf-8")


def load_schema(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise TypeError(f"Expected object schema in {path}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="append",
        choices=sorted(SCHEMA_SOURCES),
        help="Specific release line(s) to generate",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Override the source document (requires exactly one --version)",
    )
    parser.add_argument(
        "--release-repository",
        type=Path,
        help="Upstream NetBox Git checkout containing each pinned release tag",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify immutable source and deterministically regenerate artifacts without modifying them",
    )
    args = parser.parse_args()
    versions = args.version or sorted(SCHEMA_SOURCES)
    if args.source is not None and len(versions) != 1:
        parser.error("--source requires exactly one --version")
    for version in versions:
        source = args.source or SCHEMA_SOURCES[version]
        if not source.exists():
            raise FileNotFoundError(f"Schema source not found: {source}")
        if version in RELEASE_PROVENANCE and args.release_repository is None:
            parser.error(
                f"--release-repository is required to verify immutable NetBox {version} provenance"
            )
        validate_release_source(
            version,
            source,
            release_repository=args.release_repository,
        )
        version_suffix = version.replace(".", "_")
        bundled_path = OPENAPI_ROOT / f"netbox-openapi-{version}.json"
        if args.verify_only:
            if not bundled_path.is_file():
                raise FileNotFoundError(f"Bundled schema not found: {bundled_path}")
            validate_release_bundle(version, source, bundled_path)
            validate_release_artifact_hashes(version, bundled_path)
            continue
        schema = load_schema(source)
        bundled_path.parent.mkdir(parents=True, exist_ok=True)
        if version in BYTE_FAITHFUL_RELEASE_BUNDLE_VERSIONS:
            shutil.copyfile(source, bundled_path)
        else:
            bundled_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        validate_release_bundle(version, source, bundled_path)
        model_output = MODELS_ROOT / f"v{version_suffix}.py"
        generate_models(version, bundled_path, model_output)
        _prepend_models_module_doc(model_output, version)
        typed_output = TYPED_ROOT / f"v{version_suffix}.py"
        # Bindings are generated from the background-overlaid schema so the typed
        # surface can reach 4.7's background bulk mode; the committed bundle above
        # is untouched and stays byte-faithful to upstream.
        typed_output.write_text(
            build_bindings(version, apply_background_bulk_overlay(version, schema)),
            encoding="utf-8",
        )
        format_generated_artifacts([model_output, typed_output])
        write_release_provenance(
            version,
            source_path=source,
            release_repository=args.release_repository,
            bundled_path=bundled_path,
            model_path=model_output,
            typed_path=typed_output,
        )


if __name__ == "__main__":
    main()
