"""Versioned discovery contract for semantic tools exposed by NetBox plugins.

Plugins advertise an MCP bridge manifest from their normal REST API root. The
SDK treats every advertised document as hostile input: links remain same-origin,
tool targets remain under the advertising plugin namespace, schemas and payloads
are bounded, and schema references are excluded from bridge v1 so validation can
never trigger an outbound fetch.
"""

from __future__ import annotations

import asyncio
import json
import posixpath
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal, cast
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator, FormatChecker, validators
from jsonschema.exceptions import SchemaError
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.exceptions import ResponseSizeLimitError
from netbox_sdk.http_cache import QueryParams

BRIDGE_SCHEMA_VERSION = "1"
BRIDGE_ADVERTISEMENT_KEY = "mcp"
PLUGIN_API_ROOT = "/api/plugins/"
MAX_MANIFEST_BYTES = 256 * 1024
MAX_ROOT_DOCUMENT_BYTES = 1024 * 1024
MAX_SCHEMA_BYTES = 64 * 1024
MAX_SCHEMA_DEPTH = 16
MAX_SCHEMA_NODES = 2048
MAX_INSTANCE_BYTES = 256 * 1024
MAX_INSTANCE_DEPTH = 32
MAX_INSTANCE_NODES = 10_000
MAX_TOOLS_PER_MANIFEST = 64
MAX_PLUGIN_ROOTS = 128
MAX_CATALOG_TOOLS = 512
MAX_DISCOVERY_REQUESTS = 1 + (MAX_PLUGIN_ROOTS * 2)
MAX_CATALOG_BYTES = 2 * 1024 * 1024
MAX_DISCOVERY_SECONDS = 30.0
MAX_DOCUMENT_DEPTH = 24
MAX_DOCUMENT_NODES = 12_000
MAX_PROBLEM_MESSAGE_LENGTH = 2_000
MAX_SAFE_JSON_INTEGER = (2**53) - 1

_PLUGIN_NAME_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"
_TOOL_NAME_PATTERN = r"^[a-z][a-z0-9_]{0,63}$"
_RELATIVE_PATH_RE = re.compile(r"^[A-Za-z0-9._~/-]+$")
_SUPPORTED_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"})
_READ_METHODS = frozenset({"GET", "HEAD"})
_SUPPORTED_FORMATS = frozenset({"date-time"})
_RFC3339_DATE_TIME_RE = re.compile(
    r"^\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])"
    r"[Tt](?:[01]\d|2[0-3]):[0-5]\d:(?:[0-5]\d|60)(?:\.\d+)?"
    r"(?:[Zz]|[+-](?:[01]\d|2[0-3]):[0-5]\d)$"
)
_UNSUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "$defs",
        "$dynamicRef",
        "$recursiveRef",
        "$ref",
        "allOf",
        "anyOf",
        "contains",
        "dependentSchemas",
        "else",
        "if",
        "not",
        "oneOf",
        "pattern",
        "patternProperties",
        "prefixItems",
        "then",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)
_SINGLE_CHILD_SCHEMA_KEYS = frozenset(
    {"additionalProperties", "items", "propertyNames", "contentSchema"}
)
_SUPPORTED_SCHEMA_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "const",
        "default",
        "deprecated",
        "description",
        "enum",
        "examples",
        "exclusiveMaximum",
        "exclusiveMinimum",
        "format",
        "items",
        "maxItems",
        "maxLength",
        "maxProperties",
        "maximum",
        "minItems",
        "minLength",
        "minProperties",
        "minimum",
        "multipleOf",
        "properties",
        "propertyNames",
        "readOnly",
        "required",
        "title",
        "type",
        "uniqueItems",
        "writeOnly",
    }
)

PluginName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=_PLUGIN_NAME_PATTERN,
    ),
]
ToolName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=_TOOL_NAME_PATTERN,
    ),
]
JsonSchema = dict[str, Any]


class PluginBridgeError(ValueError):
    """Raised when an advertised bridge contract cannot be trusted or used."""


class _DiscoveryBudgetError(PluginBridgeError):
    """Raised when aggregate discovery bounds are exhausted."""


class _StrictContractModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        strict=True,
        str_strip_whitespace=True,
    )


def _bounded_json_walk(
    value: object,
    *,
    label: str,
    max_bytes: int,
    max_depth: int,
    max_nodes: int,
) -> None:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ValueError(f"{label} must be finite JSON data") from exc
    if len(encoded) > max_bytes:
        raise ValueError(f"{label} exceeds the {max_bytes}-byte size limit")

    nodes = 0
    stack: list[tuple[object, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > max_nodes:
            raise ValueError(f"{label} exceeds the {max_nodes}-node limit")
        if depth > max_depth:
            raise ValueError(f"{label} exceeds the maximum nesting depth {max_depth}")
        if isinstance(current, dict):
            for key, nested in current.items():
                if not isinstance(key, str):
                    raise ValueError(f"{label} object keys must be strings")
                stack.append((nested, depth + 1))
        elif isinstance(current, list):
            stack.extend((nested, depth + 1) for nested in current)


def _validate_schema_keywords(value: JsonSchema, *, label: str) -> None:
    """Reject bridge-v1 keywords that can fetch, recurse, or amplify work."""
    stack: list[object] = [value]
    while stack:
        schema = stack.pop()
        if isinstance(schema, bool):
            continue
        if not isinstance(schema, dict):
            raise ValueError(f"{label} contains a non-object child schema")
        unsupported = sorted(_UNSUPPORTED_SCHEMA_KEYWORDS.intersection(schema))
        if unsupported:
            rendered = ", ".join(unsupported)
            raise ValueError(
                f"bridge v1 does not support JSON Schema references, patterns, "
                f"or combinators ({rendered})"
            )
        unknown = sorted(set(schema).difference(_SUPPORTED_SCHEMA_KEYWORDS))
        if unknown:
            raise ValueError(
                "bridge v1 does not support JSON Schema keyword(s): " + ", ".join(unknown)
            )
        schema_format = schema.get("format")
        if schema_format is not None and (
            not isinstance(schema_format, str) or schema_format not in _SUPPORTED_FORMATS
        ):
            raise ValueError(f"bridge v1 does not support the {schema_format!r} format")
        if schema.get("uniqueItems") is True:
            items = schema.get("items")
            item_types = _schema_types(items) if isinstance(items, dict) else set()
            if len(item_types) != 1 or not item_types <= {
                "string",
                "integer",
                "number",
                "boolean",
                "null",
            }:
                raise ValueError(
                    "bridge v1 supports uniqueItems only for one explicitly typed "
                    "scalar item domain"
                )
        properties = schema.get("properties")
        if isinstance(properties, dict):
            stack.extend(properties.values())
        for key in _SINGLE_CHILD_SCHEMA_KEYS:
            child = schema.get(key)
            if isinstance(child, (dict, bool)):
                stack.append(child)


def _schema_types(schema: JsonSchema) -> set[str]:
    declared = schema.get("type")
    if isinstance(declared, str):
        return {declared}
    if isinstance(declared, list) and all(isinstance(item, str) for item in declared):
        return {str(item) for item in declared}
    return set()


def _query_schema_is_encodable(schema: JsonSchema) -> bool:
    properties = schema.get("properties", {})
    if not isinstance(properties, dict):
        return False
    scalar_types = {"string", "integer", "number", "boolean", "null"}
    for property_schema in properties.values():
        if not isinstance(property_schema, dict):
            return False
        types = _schema_types(property_schema)
        if not types:
            return False
        if types <= scalar_types:
            continue
        if not types <= {"array", "null"} or "array" not in types:
            return False
        items = property_schema.get("items")
        if not isinstance(items, dict):
            return False
        item_types = _schema_types(items)
        if not item_types or not item_types <= scalar_types:
            return False
    return True


def _validate_schema(value: JsonSchema, *, label: str, require_object: bool) -> JsonSchema:
    _bounded_json_walk(
        value,
        label=label,
        max_bytes=MAX_SCHEMA_BYTES,
        max_depth=MAX_SCHEMA_DEPTH,
        max_nodes=MAX_SCHEMA_NODES,
    )
    _validate_schema_keywords(value, label=label)
    try:
        Draft202012Validator.check_schema(value)
    except SchemaError as exc:
        raise ValueError(f"{label} must be valid Draft 2020-12 JSON Schema: {exc.message}") from exc
    if require_object:
        if value.get("type") != "object":
            raise ValueError(f"{label} must declare type=object")
        if value.get("additionalProperties") is not False:
            raise ValueError(f"{label} must set additionalProperties=false")
    return value


class PluginBridgeAdvertisement(_StrictContractModel):
    """Link advertised under the plugin API root's ``mcp`` key."""

    schema_version: Literal["1"]
    manifest: str = Field(min_length=1, max_length=2048)


class PluginToolAnnotations(_StrictContractModel):
    """MCP-compatible behavioral hints for one semantic plugin operation."""

    read_only_hint: bool = Field(alias="readOnlyHint")
    destructive_hint: bool = Field(alias="destructiveHint")
    idempotent_hint: bool = Field(alias="idempotentHint")
    open_world_hint: bool = Field(alias="openWorldHint")


class PluginTool(_StrictContractModel):
    """A semantic tool backed by one fixed plugin-local REST endpoint."""

    name: ToolName
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    method: Literal["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
    path: str = Field(min_length=2, max_length=1024)
    effect: Literal["read", "write", "destructive"]
    input_schema: JsonSchema = Field(alias="inputSchema")
    output_schema: JsonSchema | None = Field(default=None, alias="outputSchema")
    annotations: PluginToolAnnotations

    @field_validator("method", mode="before")
    @classmethod
    def _normalize_method(cls, value: object) -> str:
        method = str(value).strip().upper()
        if method not in _SUPPORTED_METHODS:
            raise ValueError(f"unsupported HTTP method: {method}")
        return method

    @field_validator("path")
    @classmethod
    def _validate_relative_path(cls, value: str) -> str:
        path = value.strip()
        if path.startswith("/") or "://" in path:
            raise ValueError("tool path must be relative to the advertising plugin API root")
        if any(character in path for character in ("\\", "?", "#", "\r", "\n", "\x00", "%")):
            raise ValueError("tool path contains an ambiguous or unsupported character")
        if not _RELATIVE_PATH_RE.fullmatch(path):
            raise ValueError("tool path contains unsupported characters")
        if not path.endswith("/"):
            raise ValueError("tool path must end with a slash")
        segments = path.split("/")[:-1]
        if not segments or any(segment in ("", ".", "..") for segment in segments):
            raise ValueError("tool path must contain only non-empty, non-dot segments")
        if posixpath.normpath(path) != path.rstrip("/"):
            raise ValueError("tool path must already be normalized")
        return path

    @field_validator("input_schema")
    @classmethod
    def _validate_input_schema(cls, value: JsonSchema) -> JsonSchema:
        return _validate_schema(value, label="inputSchema", require_object=True)

    @field_validator("output_schema")
    @classmethod
    def _validate_output_schema(cls, value: JsonSchema | None) -> JsonSchema | None:
        if value is None:
            return None
        return _validate_schema(value, label="outputSchema", require_object=False)

    @model_validator(mode="after")
    def _validate_effect_contract(self) -> PluginTool:
        is_read_method = self.method in _READ_METHODS
        if (self.effect == "read") != is_read_method:
            raise ValueError(
                "read effects require GET/HEAD and write effects require a write method"
            )
        if self.method == "DELETE" and self.effect != "destructive":
            raise ValueError("DELETE tools must declare effect=destructive")
        if self.annotations.read_only_hint != (self.effect == "read"):
            raise ValueError("readOnlyHint must match the declared effect")
        if self.annotations.destructive_hint != (self.effect == "destructive"):
            raise ValueError("destructiveHint must match the declared effect")
        if is_read_method and not _query_schema_is_encodable(self.input_schema):
            raise ValueError(
                "GET/HEAD inputSchema properties must be query-encodable scalars "
                "or arrays of scalars"
            )
        return self


class PluginManifest(_StrictContractModel):
    """Bridge v1 manifest returned by an advertising NetBox plugin."""

    schema_version: Literal["1"]
    plugin: PluginName
    tools: list[PluginTool] = Field(min_length=1, max_length=MAX_TOOLS_PER_MANIFEST)

    @model_validator(mode="after")
    def _validate_unique_tools(self) -> PluginManifest:
        names = [tool.name for tool in self.tools]
        if len(names) != len(set(names)):
            raise ValueError("tool names must be unique within a plugin manifest")
        return self


@dataclass(frozen=True)
class PluginManifestProblem:
    """One plugin advertisement that failed closed during catalog discovery."""

    plugin: str
    error: str


@dataclass(frozen=True)
class PluginManifestCatalog:
    """Validated manifests plus isolated problems from an all-plugin scan."""

    manifests: tuple[PluginManifest, ...]
    problems: tuple[PluginManifestProblem, ...] = ()

    def find_tool(self, plugin: str, tool: str) -> PluginTool:
        for manifest in self.manifests:
            if manifest.plugin != plugin:
                continue
            for descriptor in manifest.tools:
                if descriptor.name == tool:
                    return descriptor
            raise PluginBridgeError(f"Plugin tool not found: {plugin}.{tool}")
        for problem in self.problems:
            if problem.plugin == plugin:
                raise PluginBridgeError(problem.error)
        raise PluginBridgeError(f"Plugin does not advertise an MCP bridge: {plugin}")


class _PluginSelector(_StrictContractModel):
    plugin: PluginName


def _validation_error_summary(exc: ValidationError) -> str:
    """Render bounded validation details without echoing hostile input values."""
    summaries: list[str] = []
    for error in exc.errors(include_input=False, include_url=False)[:10]:
        location = ".".join(str(part) for part in error.get("loc", ())) or "document"
        summaries.append(f"{location}: {error.get('msg', 'invalid value')}")
    rendered = "; ".join(summaries) or "invalid contract"
    return rendered[:MAX_PROBLEM_MESSAGE_LENGTH]


@dataclass
class _DiscoveryBudget:
    requests: int = 0
    response_bytes: int = 0

    def begin_request(self) -> None:
        self.requests += 1
        if self.requests > MAX_DISCOVERY_REQUESTS:
            raise _DiscoveryBudgetError(
                f"plugin discovery exceeds the {MAX_DISCOVERY_REQUESTS}-request limit"
            )

    def add_response(self, byte_count: int) -> None:
        self.response_bytes += byte_count
        if self.response_bytes > MAX_CATALOG_BYTES:
            raise _DiscoveryBudgetError(
                f"plugin discovery exceeds the {MAX_CATALOG_BYTES}-byte aggregate limit"
            )

    def remaining_response_bytes(self) -> int:
        remaining = MAX_CATALOG_BYTES - self.response_bytes
        if remaining <= 0:
            raise _DiscoveryBudgetError(
                f"plugin discovery exceeds the {MAX_CATALOG_BYTES}-byte aggregate limit"
            )
        return remaining


def _origin(value: str) -> tuple[str, str, int | None]:
    parsed = urlsplit(value)
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme.lower() == "https" else 80
    return parsed.scheme.lower(), (parsed.hostname or "").casefold(), port


def _api_path_from_link(client: NetBoxApiClient, value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise PluginBridgeError(f"{label} must be a string URL or absolute API path")
    raw = value.strip()
    if not raw or any(character in raw for character in ("\\", "\r", "\n", "\x00", "%")):
        raise PluginBridgeError(f"{label} contains an ambiguous or unsupported character")
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise PluginBridgeError(f"{label} must be a well-formed URL or API path") from exc
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise PluginBridgeError(f"{label} must not contain credentials, a query, or a fragment")
    base_url = getattr(getattr(client, "config", None), "base_url", None)
    base_path = ""
    if base_url:
        try:
            base_path = urlsplit(base_url).path.rstrip("/")
        except ValueError as exc:
            raise PluginBridgeError("configured NetBox base URL is malformed") from exc
    if parsed.scheme or parsed.netloc:
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise PluginBridgeError(f"{label} must use an HTTP(S) URL")
        try:
            same_origin = bool(base_url) and _origin(raw) == _origin(base_url)
        except ValueError as exc:
            raise PluginBridgeError(f"{label} must be a well-formed URL") from exc
        if not same_origin:
            raise PluginBridgeError(f"{label} must remain on the configured NetBox origin")
    path = parsed.path
    if base_path and path.startswith(f"{base_path}/api/"):
        path = path[len(base_path) :]
    if not path.startswith("/api/") or not path.endswith("/"):
        expected = f"{base_path}/api/.../" if base_path else "/api/.../"
        raise PluginBridgeError(f"{label} must be an absolute {expected} path")
    decoded = unquote(path)
    segments = decoded.split("/")
    if decoded != path or any(segment in (".", "..") for segment in segments):
        raise PluginBridgeError(f"{label} must not contain encoded or dot segments")
    if "//" in path or posixpath.normpath(path) != path.rstrip("/"):
        raise PluginBridgeError(f"{label} must already be normalized")
    return path


def _strict_json_loads(
    text: str,
    *,
    label: str,
    max_bytes: int,
    max_depth: int = MAX_DOCUMENT_DEPTH,
    max_nodes: int = MAX_DOCUMENT_NODES,
) -> object:
    def _reject_non_finite(value: str) -> object:
        raise ValueError(f"non-finite JSON constant: {value}")

    if len(text.encode("utf-8")) > max_bytes:
        raise PluginBridgeError(f"{label} exceeds the {max_bytes}-byte size limit")
    try:
        payload = json.loads(text, parse_constant=_reject_non_finite)
    except RecursionError as exc:
        raise PluginBridgeError(f"{label} exceeds the JSON nesting limit") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        message = "must contain finite JSON" if "non-finite" in str(exc) else "is not valid JSON"
        raise PluginBridgeError(f"{label} {message}") from exc
    try:
        _bounded_json_walk(
            payload,
            label=label,
            max_bytes=max_bytes,
            max_depth=max_depth,
            max_nodes=max_nodes,
        )
    except ValueError as exc:
        raise PluginBridgeError(str(exc)) from exc
    return payload


async def _request_json_document(
    client: NetBoxApiClient,
    path: str,
    *,
    label: str,
    max_bytes: int,
    budget: _DiscoveryBudget,
) -> object:
    budget.begin_request()
    remaining_bytes = budget.remaining_response_bytes()
    response_limit = min(max_bytes, remaining_bytes)
    try:
        response = await client.request_bounded(
            "GET",
            path,
            max_response_bytes=response_limit,
        )
    except ResponseSizeLimitError as exc:
        if response_limit < max_bytes:
            raise _DiscoveryBudgetError(
                f"plugin discovery exceeds the {MAX_CATALOG_BYTES}-byte aggregate limit"
            ) from exc
        raise PluginBridgeError(f"{label} exceeds the {max_bytes}-byte size limit") from exc
    except Exception as exc:
        raise PluginBridgeError(f"{label} request failed: {type(exc).__name__}") from exc
    response_size = (
        response.body_size_bytes
        if response.body_size_bytes is not None
        else len(response.text.encode("utf-8"))
    )
    budget.add_response(response_size)
    if response.status < 200 or response.status >= 300:
        raise PluginBridgeError(f"{label} returned HTTP {response.status}")
    return _strict_json_loads(response.text, label=label, max_bytes=max_bytes)


def _plugin_slug_from_root(path: str) -> str:
    parts = [segment for segment in path.split("/") if segment]
    if len(parts) != 3 or parts[:2] != ["api", "plugins"]:
        raise PluginBridgeError("plugin root link must be /api/plugins/<slug>/")
    try:
        return _PluginSelector.model_validate({"plugin": parts[2]}).plugin
    except ValidationError as exc:
        raise PluginBridgeError("plugin API slug is invalid") from exc


async def _discover_one_manifest(
    client: NetBoxApiClient,
    *,
    plugin: str,
    plugin_root: str,
    budget: _DiscoveryBudget,
) -> PluginManifest | None:
    root_payload = await _request_json_document(
        client,
        plugin_root,
        label=f"{plugin} plugin API root",
        max_bytes=MAX_ROOT_DOCUMENT_BYTES,
        budget=budget,
    )
    if not isinstance(root_payload, dict):
        raise PluginBridgeError(f"{plugin} plugin API root must return a JSON object")
    advertisement_payload = root_payload.get(BRIDGE_ADVERTISEMENT_KEY)
    if advertisement_payload is None:
        return None
    try:
        advertisement = PluginBridgeAdvertisement.model_validate(advertisement_payload)
    except ValidationError as exc:
        raise PluginBridgeError(
            f"{plugin} MCP advertisement is invalid: {_validation_error_summary(exc)}"
        ) from exc
    manifest_path = _api_path_from_link(
        client,
        advertisement.manifest,
        label=f"{plugin} advertised manifest path",
    )
    expected_manifest_path = f"{plugin_root}mcp/"
    if manifest_path != expected_manifest_path:
        raise PluginBridgeError(
            f"{plugin} advertised manifest path must be {expected_manifest_path}"
        )
    manifest_payload = await _request_json_document(
        client,
        manifest_path,
        label=f"{plugin} MCP manifest",
        max_bytes=MAX_MANIFEST_BYTES,
        budget=budget,
    )
    try:
        manifest = PluginManifest.model_validate(manifest_payload)
    except ValidationError as exc:
        raise PluginBridgeError(
            f"{plugin} MCP manifest is invalid: {_validation_error_summary(exc)}"
        ) from exc
    if manifest.plugin != plugin:
        raise PluginBridgeError(
            f"{plugin} MCP manifest declares a different plugin: {manifest.plugin}"
        )
    return manifest


async def _discover_plugin_manifests(
    client: NetBoxApiClient,
    *,
    plugin: str | None = None,
) -> PluginManifestCatalog:
    """Discover validated bridge manifests explicitly advertised by plugin roots.

    A plugin-specific lookup raises on any contract failure. An all-plugin scan
    isolates each bad advertisement in ``problems`` so one plugin cannot hide
    valid semantic tools exposed by another.
    """
    selected = None
    budget = _DiscoveryBudget()
    if plugin is not None:
        try:
            selected = _PluginSelector.model_validate({"plugin": plugin}).plugin
        except ValidationError as exc:
            raise PluginBridgeError(f"invalid plugin name: {plugin}") from exc

    root_payload = await _request_json_document(
        client,
        PLUGIN_API_ROOT,
        label="NetBox plugin API root",
        max_bytes=MAX_ROOT_DOCUMENT_BYTES,
        budget=budget,
    )
    if not isinstance(root_payload, dict):
        raise PluginBridgeError("NetBox plugin API root must return a JSON object")
    if len(root_payload) > MAX_PLUGIN_ROOTS:
        raise PluginBridgeError(f"plugin root count exceeds the {MAX_PLUGIN_ROOTS}-root limit")

    roots: dict[str, str] = {}
    root_problems: list[PluginManifestProblem] = []
    for key, raw_link in root_payload.items():
        problem_name = str(key)
        try:
            root_path = _api_path_from_link(
                client,
                raw_link,
                label=f"{problem_name} plugin root link",
            )
            slug = _plugin_slug_from_root(root_path)
            if slug in roots and roots[slug] != root_path:
                raise PluginBridgeError(f"duplicate plugin API root for {slug}")
            roots[slug] = root_path
        except PluginBridgeError as exc:
            root_problems.append(
                PluginManifestProblem(
                    plugin=problem_name[:64],
                    error=str(exc)[:MAX_PROBLEM_MESSAGE_LENGTH],
                )
            )

    if selected is not None:
        if selected not in roots:
            matching_problem = next(
                (problem for problem in root_problems if problem.plugin == selected), None
            )
            if matching_problem is not None:
                raise PluginBridgeError(matching_problem.error)
            raise PluginBridgeError(f"Plugin API root not found: {selected}")
        manifest = await _discover_one_manifest(
            client,
            plugin=selected,
            plugin_root=roots[selected],
            budget=budget,
        )
        return PluginManifestCatalog(manifests=(() if manifest is None else (manifest,)))

    manifests: list[PluginManifest] = []
    problems = list(root_problems)
    catalog_tool_count = 0
    for slug, root_path in sorted(roots.items()):
        try:
            manifest = await _discover_one_manifest(
                client,
                plugin=slug,
                plugin_root=root_path,
                budget=budget,
            )
        except _DiscoveryBudgetError:
            raise
        except PluginBridgeError as exc:
            problems.append(
                PluginManifestProblem(
                    plugin=slug,
                    error=str(exc)[:MAX_PROBLEM_MESSAGE_LENGTH],
                )
            )
            continue
        if manifest is not None:
            catalog_tool_count += len(manifest.tools)
            if catalog_tool_count > MAX_CATALOG_TOOLS:
                raise PluginBridgeError(
                    f"catalog tool count exceeds the {MAX_CATALOG_TOOLS}-tool limit"
                )
            manifests.append(manifest)
    return PluginManifestCatalog(
        manifests=tuple(manifests),
        problems=tuple(problems),
    )


async def discover_plugin_manifests(
    client: NetBoxApiClient,
    *,
    plugin: str | None = None,
) -> PluginManifestCatalog:
    """Discover current plugin manifests within one aggregate time budget."""
    try:
        async with asyncio.timeout(MAX_DISCOVERY_SECONDS):
            return await _discover_plugin_manifests(client, plugin=plugin)
    except TimeoutError as exc:
        raise PluginBridgeError(
            f"plugin discovery exceeded the {MAX_DISCOVERY_SECONDS:g}-second deadline"
        ) from exc


def plugin_tool_request_path(plugin: str, tool: PluginTool) -> str:
    """Resolve a validated relative tool target under its plugin API namespace."""
    selected = _PluginSelector.model_validate({"plugin": plugin}).plugin
    return f"/api/plugins/{selected}/{tool.path}"


def _is_rfc3339_date_time(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if _RFC3339_DATE_TIME_RE.fullmatch(value) is None:
        return False
    normalized = value.replace("t", "T").replace("z", "Z")
    leap_second = re.search(r":60(?=(?:\.\d+)?(?:Z|[+-]))", normalized) is not None
    normalized = re.sub(r":60(?=(?:\.\d+)?(?:Z|[+-]))", ":59", normalized)
    try:
        parsed = datetime.fromisoformat(normalized).astimezone(UTC)
        if leap_second:
            parsed += timedelta(seconds=1)
            if not (
                parsed.day == 1 and parsed.hour == 0 and parsed.minute == 0 and parsed.second == 0
            ):
                return False
    except (OverflowError, ValueError):
        return False
    return True


_BRIDGE_FORMAT_CHECKER = FormatChecker()
_BRIDGE_FORMAT_CHECKER.checks("date-time")(_is_rfc3339_date_time)


def _is_bridge_integer(_checker: object, value: object) -> bool:
    """Apply lossless JSON-number semantics to bridge integer schemas."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, float) and value.is_integer() and abs(value) <= MAX_SAFE_JSON_INTEGER


_BRIDGE_TYPE_CHECKER = Draft202012Validator.TYPE_CHECKER.redefine("integer", _is_bridge_integer)
_BridgeDraft202012Validator = validators.extend(
    Draft202012Validator,
    type_checker=_BRIDGE_TYPE_CHECKER,
)


def _validate_instance(instance: object, schema: JsonSchema, *, label: str) -> None:
    try:
        _bounded_json_walk(
            instance,
            label=label,
            max_bytes=MAX_INSTANCE_BYTES,
            max_depth=MAX_INSTANCE_DEPTH,
            max_nodes=MAX_INSTANCE_NODES,
        )
    except ValueError as exc:
        raise PluginBridgeError(str(exc)) from exc
    try:
        validator = _BridgeDraft202012Validator(
            schema,
            format_checker=_BRIDGE_FORMAT_CHECKER,
        )
        errors = list(validator.iter_errors(cast(Any, instance)))
    except Exception as exc:
        raise PluginBridgeError(f"{label} validation failed safely: {type(exc).__name__}") from exc
    if not errors:
        return
    error = min(
        errors,
        key=lambda candidate: tuple(str(part) for part in candidate.absolute_path),
    )
    location = ".".join(str(part) for part in error.absolute_path)
    prefix = f" at {location}" if location else ""
    raise PluginBridgeError(f"{label}{prefix}: {error.message}")


def validate_plugin_tool_arguments(tool: PluginTool, arguments: dict[str, Any]) -> None:
    """Validate bounded invocation arguments against a tool's input schema."""
    _validate_instance(arguments, tool.input_schema, label=f"{tool.name} arguments")


def validate_plugin_tool_response(tool: PluginTool, body: object) -> None:
    """Bound every successful response and apply its declared schema, if any."""
    if tool.output_schema is not None:
        _validate_instance(body, tool.output_schema, label=f"{tool.name} response")
        return
    try:
        _bounded_json_walk(
            body,
            label=f"{tool.name} response",
            max_bytes=MAX_INSTANCE_BYTES,
            max_depth=MAX_INSTANCE_DEPTH,
            max_nodes=MAX_INSTANCE_NODES,
        )
    except ValueError as exc:
        raise PluginBridgeError(str(exc)) from exc


def validate_plugin_tool_response_document(text: str) -> None:
    """Validate a bounded tool response as strict, finite JSON."""
    parse_plugin_tool_response_document(text)


def parse_plugin_tool_response_document(text: str) -> object:
    """Parse a bridge response with uniform size, depth, node, and finite bounds."""
    return _strict_json_loads(
        text,
        label="plugin tool response",
        max_bytes=MAX_INSTANCE_BYTES,
        max_depth=MAX_INSTANCE_DEPTH,
        max_nodes=MAX_INSTANCE_NODES,
    )


def plugin_arguments_to_query(arguments: dict[str, Any]) -> QueryParams:
    """Convert validated scalar/list arguments into deterministic HTTP query values."""

    def _scalar(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (str, int, float)):
            return str(value)
        raise PluginBridgeError("read-tool arguments must be scalars or lists of scalars")

    query: QueryParams = {}
    for name, value in arguments.items():
        if isinstance(value, list):
            query[name] = [_scalar(item) for item in value]
        else:
            query[name] = _scalar(value)
    return query
