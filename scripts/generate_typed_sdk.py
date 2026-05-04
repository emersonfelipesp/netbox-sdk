"""Generate versioned Pydantic models and typed bindings from NetBox OpenAPI schemas."""

from __future__ import annotations

import argparse
import json
import keyword
import os
import re
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

SCHEMA_SOURCES = {
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
    mapping = {
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "string": "str",
        "object": "dict[str, Any]",
    }
    return mapping.get(schema_type, "Any")


@dataclass
class OperationSpec:
    method: str
    operation_id: str
    path: str
    method_name: str
    query_model_name: str | None
    body_model_expr: str | None
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


def request_body_expr(operation: dict[str, Any]) -> str | None:
    body = operation.get("requestBody")
    if not isinstance(body, dict):
        return None
    content = body.get("content")
    if not isinstance(content, dict):
        return None
    for media_type in ("application/json", "multipart/form-data"):
        media = content.get(media_type)
        if isinstance(media, dict):
            schema = media.get("schema")
            if isinstance(schema, dict):
                return type_expr(schema)
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
        class_key = pascal_case(f"{group}_{resource}_{action_name or 'root'}")

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
                query_models[query_model_name] = render_query_model(query_model_name, params)
            body_expr = request_body_expr(operation)
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
                body_model_expr=body_expr,
                response_model_expr=response_model_expr,
                raw_response=raw_response,
                path_param_names=path_param_names(path),
            )
            resource_key = resource if not action_name else f"{resource}:{action_name}"
            per_group_resources[group][resource_key].append(spec)

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
        "from netbox_sdk.typed_runtime import TypedApiBase, TypedAppBase, build_typed_client",
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
                    params.append(f"body: {spec.body_model_expr}")
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
                    lines.append(
                        f"        return await self._typed_json_request({spec.method!r}, path, {', '.join(kwargs)})"
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


def generate_models(version: str, input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")
    env.setdefault("UV_TOOL_DIR", "/tmp/uv-tools")
    subprocess.run(
        [
            "uvx",
            "--from",
            "datamodel-code-generator",
            "datamodel-codegen",
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
        ],
        check=True,
        env=env,
    )


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
        version_suffix = version.replace(".", "_")
        bundled_path = OPENAPI_ROOT / f"netbox-openapi-{version}.json"
        bundled_path.parent.mkdir(parents=True, exist_ok=True)
        schema = load_schema(source)
        bundled_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        model_output = MODELS_ROOT / f"v{version_suffix}.py"
        generate_models(version, bundled_path, model_output)
        _prepend_models_module_doc(model_output, version)
        typed_output = TYPED_ROOT / f"v{version_suffix}.py"
        typed_output.write_text(build_bindings(version, schema), encoding="utf-8")


if __name__ == "__main__":
    main()
