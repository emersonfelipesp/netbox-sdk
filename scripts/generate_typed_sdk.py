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
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SDK_ROOT = REPO_ROOT / "netbox_sdk"
MODELS_ROOT = SDK_ROOT / "models"
TYPED_ROOT = SDK_ROOT / "typed_versions"
OPENAPI_ROOT = SDK_ROOT / "reference" / "openapi"
DATAMODEL_CODE_GENERATOR_VERSION = "0.55.0"
RUFF_VERSION = "0.15.9"

RELEASE_PROVENANCE: dict[str, dict[str, str]] = {
    "4.7": {
        "netbox_release": "v4.7.0-beta2",
        "release_commit": "aa1d49d0f5021a28e6efc2d0364b84c5bcec7137",
        "source_path": "contrib/openapi.json",
        "source_blob_sha": "1a3e6621a50520515652f969e9736da2545704c2",
        "source_sha256": "1408f6421f45720ecf25aa0edb777f185f74f9a87af887b5eeb73fee8012b880",
        "source_url": "https://github.com/netbox-community/netbox/blob/v4.7.0-beta2/contrib/openapi.json",
    },
    "4.6": {
        "netbox_release": "v4.6.6",
        "release_commit": "fb8c455ba61b57119a70670612dfdd05e8438b10",
        "source_path": "contrib/openapi.json",
        "source_blob_sha": "024d34500a04ec876fb3b32fa18c685e953a02f8",
        "source_sha256": "c1a3e2dee07a7a5bfedd9221c3495597cd2624baa32695800d1f75edbc5c044e",
        "source_url": "https://github.com/netbox-community/netbox/blob/v4.6.6/contrib/openapi.json",
    },
}

SCHEMA_SOURCES = {
    "4.7": Path("/tmp/netbox-v4.7.0-beta2-openapi.json"),
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


def path_param_names(path: str) -> tuple[str, ...]:
    return tuple(re.findall(r"{([^}]+)}", path))


def build_bindings(version: str, schema: dict[str, Any]) -> str:
    suffix = version.replace(".", "_")
    per_group_resources: dict[str, dict[str, list[OperationSpec]]] = defaultdict(
        lambda: defaultdict(list)
    )
    query_models: dict[str, str] = {}
    list_detail_pairs: dict[tuple[str, str], dict[str, str]] = defaultdict(dict)
    components = schema.get("components", {}).get("schemas", {})
    if not isinstance(components, dict):
        components = {}

    for path, path_item in schema.get("paths", {}).items():
        if not isinstance(path_item, dict) or not path.startswith("/api/"):
            continue
        parts = [part for part in path.split("/") if part]
        if len(parts) < 3:
            continue
        group = snake_case(parts[1])
        resource = snake_case(parts[2])
        is_detail = len(parts) >= 4 and parts[3].startswith("{") and parts[3].endswith("}")
        is_action = len(parts) > (4 if is_detail else 3)
        if not is_action:
            list_detail_pairs[(group, resource)]["detail" if is_detail else "list"] = path

        action_parts = parts[4:] if is_detail else parts[3:]
        action_name = snake_case("_".join(action_parts)) if action_parts else ""
        query_scope = action_name or ("detail" if is_detail else "root")
        class_key = pascal_case(f"{group}_{resource}_{query_scope}")

        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue
            params = [
                param
                for param in operation.get("parameters", [])
                if isinstance(param, dict) and param.get("in") == "query"
            ]
            query_model_name = None
            if params:
                query_model_name = f"{class_key}{pascal_case(method)}Query"
                rendered_query = render_query_model(query_model_name, params)
                existing_query = query_models.get(query_model_name)
                if existing_query is not None and existing_query != rendered_query:
                    raise ValueError(
                        f"Conflicting query model {query_model_name!r} generated for "
                        f"{method.upper()} {path}"
                    )
                query_models[query_model_name] = rendered_query
            body_spec = request_body_spec(operation, components)
            response_model_expr, raw_response = response_expr(operation)
            method_name = None
            if is_action:
                method_name = {
                    "get": "list",
                    "post": "create",
                    "put": "update",
                    "patch": "partial_update",
                    "delete": "delete",
                }.get(method.lower())
            if method_name is None:
                method_name = SPECIAL_METHOD_NAMES.get((method.lower(), is_detail, is_action))
            if method_name is None:
                method_name = snake_case(
                    operation.get("operationId") or f"{method}_{action_name or 'call'}"
                )
            spec = OperationSpec(
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
            )
            resource_key = resource if not action_name else f"{resource}:{action_name}"
            per_group_resources[group][resource_key].append(spec)

    raw_plugin_fallback = "plugins" not in per_group_resources
    runtime_imports = ["TypedApiBase", "TypedAppBase", "build_typed_client"]
    if raw_plugin_fallback:
        runtime_imports.insert(0, "RawBranchingApp")

    imports = [
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
    body = []
    if query_models:
        for model_name in sorted(query_models):
            body.append(query_models[model_name])
            body.append("")

    endpoint_classes: list[str] = []
    app_classes: list[str] = []
    api_assignments: list[str] = []

    for group in sorted(per_group_resources):
        root_resources = sorted(key for key in per_group_resources[group] if ":" not in key)
        child_map: dict[str, list[str]] = defaultdict(list)
        for key in per_group_resources[group]:
            if ":" in key:
                parent, child = key.split(":", 1)
                child_map[parent].append(child)

        generated_classes: dict[str, str] = {}
        for resource_key, operations in sorted(per_group_resources[group].items()):
            resource_name, _, action_name = resource_key.partition(":")
            class_name = pascal_case(f"{group}_{resource_name}_{action_name or 'endpoint'}")
            lines = [
                f"class {class_name}(TypedAppBase):",
                f'    """Typed OpenAPI resource `{group}/{resource_key}` for NetBox {version}."""',
            ]
            lines.append("    def __init__(self, api: TypedApiBase) -> None:")
            lines.append("        super().__init__(api)")
            lines.append("")
            if not action_name:
                for child in sorted(child_map.get(resource_name, [])):
                    child_class = pascal_case(f"{group}_{resource_name}_{child}")
                    attr_name = snake_case(child)
                    lines.append("    @property")
                    lines.append(f"    def {attr_name}(self) -> {child_class}:")
                    lines.append(f"        return {child_class}(self._api)")
                    lines.append("")
            for spec in operations:
                path_params = []
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
                signature = ", ".join(params)
                return_expr = spec.response_model_expr or "None"
                if spec.method_name == "get" and spec.response_model_expr is not None:
                    return_expr = f"{return_expr} | None"
                lines.append(f"    async def {spec.method_name}({signature}) -> {return_expr}:")
                if spec.path_param_names:
                    lines.append(f'        path = f"{path_expr}"')
                else:
                    lines.append(f'        path = "{path_expr}"')
                if spec.raw_response:
                    query_arg = "query=query" if spec.query_model_name is not None else "query=None"
                    query_model = spec.query_model_name or "None"
                    lines.append(
                        f"        return await self._typed_raw_request({spec.method!r}, path, query_model={query_model}, {query_arg})"
                    )
                else:
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
                    lines.append(
                        f"        return await self.{request_method}({spec.method!r}, path, "
                        f"{', '.join(kwargs)})"
                    )
                lines.append("")
            if len(lines) == 4:
                lines.append("    pass")
                lines.append("")
            generated_classes[resource_key] = "\n".join(lines)

        for resource_key in sorted(generated_classes):
            endpoint_classes.append(generated_classes[resource_key])
            endpoint_classes.append("")

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
            lines.append("    @property")
            lines.append(f"    def {resource}(self) -> {endpoint_class}:")
            lines.append(f"        return {endpoint_class}(self._api)")
            lines.append("")
        if len(lines) == 4:
            lines.append("    pass")
            lines.append("")
        app_classes.append("\n".join(lines))
        app_classes.append("")
        api_assignments.append(f"        self.{group} = {app_class_name}(self)")

    if raw_plugin_fallback:
        app_classes.extend(
            [
                "\n".join(
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
                ),
                "",
            ]
        )
        api_assignments.append("        self.plugins = PluginsApp(self)")

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
    return "\n".join(imports + body + endpoint_classes + app_classes + api_lines + factory_lines)


# ---------------------------------------------------------------------------
# Write-compatibility overlay
# ---------------------------------------------------------------------------
# NetBox 4.7 declares the legacy single-protocol ``protocol``/``ports`` pair on a
# *shared* serializer that Service and ServiceTemplate inherit from. The bundled
# upstream schema documents the write contract explicitly:
#
#   "Write: either format is accepted. When the legacy ``protocol``/``ports``
#    pair is supplied (and ``port_mappings`` is not), it is translated into
#    ``port_mappings``."
#
# but drf-spectacular's introspection does not emit ``protocol`` into the
# writable models' ``properties`` block (``ports`` *is* emitted). Generating
# straight from ``properties`` therefore produces writable models that silently
# DROP a field the REST API accepts. That is not a cosmetic gap: a PATCH of
# ``{"protocol": "udp", "ports": [53]}`` would be sent as ``{"ports": [53]}``,
# and NetBox backfills the stored protocol - turning an intended tcp->udp change
# into ``tcp/53``.
#
# The overlay restores those fields for model generation ONLY. It is applied to
# an in-memory copy; the committed ``netbox-openapi-*.json`` stays byte-faithful
# to the pinned upstream artifact, so provenance verification is unaffected.
# Each entry is deterministic and copies the field definition from the
# corresponding read-side request model rather than inventing a schema.
WRITE_COMPAT_OVERLAY: dict[str, dict[str, tuple[str, ...]]] = {
    "4.7": {
        "WritableServiceRequest": ("protocol",),
        "PatchedWritableServiceRequest": ("protocol",),
        "WritableServiceTemplateRequest": ("protocol",),
        "PatchedWritableServiceTemplateRequest": ("protocol",),
    }
}

# Where each overlaid model borrows its field definition from.
_OVERLAY_FIELD_SOURCE = {
    "WritableServiceRequest": "ServiceRequest",
    "PatchedWritableServiceRequest": "ServiceRequest",
    "WritableServiceTemplateRequest": "ServiceTemplateRequest",
    "PatchedWritableServiceTemplateRequest": "ServiceTemplateRequest",
}


# Background bulk-operation overlay
# ---------------------------------------------------------------------------
# NetBox 4.7 adds ``?background=true`` to bulk POST/PUT/PATCH/DELETE on collection
# paths, answering 202 with a job reference instead of executing synchronously.
# It exists specifically to avoid proxy timeouts on large batches.
#
# The pinned upstream artifact is ``v4.7.0-beta2``, whose OpenAPI document does
# not describe the capability at all (0 ``background`` parameters, 0 ``202``
# responses -- asserted by a guard test). The generated bindings are therefore
# *faithful to the artifact*, and the typed surface simply cannot reach a feature
# the raw client can already use.
#
# This is a distinct mechanism from WRITE_COMPAT_OVERLAY above, which patches
# component-schema *properties*. This one patches *operations*, adding a query
# parameter, so the generated query model exposes it.
#
# Remove this the moment upstream's GA schema describes the parameter; the guard
# test in tests/test_typed_background_bulk.py fails if the overlay outlives its
# reason to exist.
BACKGROUND_BULK_OVERLAY_VERSIONS: frozenset[str] = frozenset({"4.7"})

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


def apply_write_compat_overlay(version: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of ``schema`` with REST-writable legacy fields restored.

    Raises:
        KeyError: If an overlay target or its field source is missing, which means
            the upstream schema changed shape and the overlay needs review rather
            than silent skipping.
    """
    overlay = WRITE_COMPAT_OVERLAY.get(version)
    if not overlay:
        return schema
    patched = json.loads(json.dumps(schema))
    components = patched["components"]["schemas"]
    for model, fields in overlay.items():
        target = components[model]
        source = components[_OVERLAY_FIELD_SOURCE[model]]
        for field in fields:
            if field in target.get("properties", {}):
                continue
            target.setdefault("properties", {})[field] = json.loads(
                json.dumps(source["properties"][field])
            )
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


def validate_release_source(version: str, source_path: Path) -> None:
    """Reject release inputs that do not match the pinned official artifact."""

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


def write_release_provenance(
    version: str,
    *,
    source_path: Path,
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
    validate_release_source(version, source_path)

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
    args = parser.parse_args()
    versions = args.version or sorted(SCHEMA_SOURCES)
    for version in versions:
        source = SCHEMA_SOURCES[version]
        if not source.exists():
            raise FileNotFoundError(f"Schema source not found: {source}")
        validate_release_source(version, source)
        version_suffix = version.replace(".", "_")
        bundled_path = OPENAPI_ROOT / f"netbox-openapi-{version}.json"
        bundled_path.parent.mkdir(parents=True, exist_ok=True)
        schema = load_schema(source)
        # The committed bundle stays byte-faithful to upstream; the overlay is
        # applied only to the copy that model generation reads.
        bundled_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        model_output = MODELS_ROOT / f"v{version_suffix}.py"
        overlaid = apply_write_compat_overlay(version, schema)
        if overlaid is schema:
            generate_models(version, bundled_path, model_output)
        else:
            overlay_path = bundled_path.with_name(f"{bundled_path.stem}.overlaid.json")
            overlay_path.write_text(json.dumps(overlaid, indent=2), encoding="utf-8")
            try:
                generate_models(version, overlay_path, model_output)
            finally:
                overlay_path.unlink(missing_ok=True)
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
            bundled_path=bundled_path,
            model_path=model_output,
            typed_path=typed_output,
        )


if __name__ == "__main__":
    main()
