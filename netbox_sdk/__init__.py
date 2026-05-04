"""netbox-sdk — Standalone NetBox REST API client library."""

from __future__ import annotations

__all__ = [
    "__version__",
    # config
    "Config",
    "DEFAULT_PROFILE",
    "DEMO_PROFILE",
    "DEMO_BASE_URL",
    "config_path",
    "cache_dir",
    "load_config",
    "load_profile_config",
    "save_config",
    "save_profile_config",
    "clear_profile_config",
    "normalize_base_url",
    "authorization_header_value",
    "resolved_token",
    "is_runtime_config_complete",
    # client
    "NetBoxApiClient",
    "ApiResponse",
    "RequestError",
    "ConnectionProbe",
    "api",
    "Api",
    "App",
    "PluginsApp",
    "Endpoint",
    "DetailEndpoint",
    "RODetailEndpoint",
    "ROMultiFormatDetailEndpoint",
    "Record",
    "RecordSet",
    "ContentError",
    "AllocationError",
    "ParameterValidationError",
    "JsonPayloadError",
    "typed_api",
    "SupportedNetBoxVersion",
    "SUPPORTED_NETBOX_VERSIONS",
    "UnsupportedNetBoxVersionError",
    "TypedRequestValidationError",
    "TypedResponseValidationError",
    # http_cache
    "HttpCacheStore",
    "CachePolicy",
    "CacheEntry",
    "build_cache_key",
    # schema
    "SchemaIndex",
    "Operation",
    "ResourcePaths",
    "FilterParam",
    "parse_group_resource",
    "load_openapi_schema",
    "build_schema_index",
    # services
    "ResolvedRequest",
    "resolve_dynamic_request",
    "run_dynamic_command",
    "parse_key_value_pairs",
    "load_json_payload",
    "ACTION_METHOD_MAP",
    # plugin_discovery
    "discover_plugin_resource_paths",
]

__version__ = "0.0.7.post6"

from netbox_sdk.client import ApiResponse, ConnectionProbe, NetBoxApiClient
from netbox_sdk.config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    authorization_header_value,
    cache_dir,
    clear_profile_config,
    config_path,
    is_runtime_config_complete,
    load_config,
    load_profile_config,
    normalize_base_url,
    resolved_token,
    save_config,
    save_profile_config,
)
from netbox_sdk.exceptions import (
    AllocationError,
    ContentError,
    JsonPayloadError,
    ParameterValidationError,
    RequestError,
)
from netbox_sdk.facade import (
    Api,
    App,
    DetailEndpoint,
    Endpoint,
    PluginsApp,
    Record,
    RecordSet,
    RODetailEndpoint,
    ROMultiFormatDetailEndpoint,
    api,
)
from netbox_sdk.http_cache import CacheEntry, CachePolicy, HttpCacheStore, build_cache_key
from netbox_sdk.plugin_discovery import discover_plugin_resource_paths
from netbox_sdk.schema import (
    FilterParam,
    Operation,
    ResourcePaths,
    SchemaIndex,
    build_schema_index,
    load_openapi_schema,
    parse_group_resource,
)
from netbox_sdk.typed_api import typed_api
from netbox_sdk.typed_runtime import TypedRequestValidationError, TypedResponseValidationError
from netbox_sdk.versioning import (
    SUPPORTED_NETBOX_VERSIONS,
    SupportedNetBoxVersion,
    UnsupportedNetBoxVersionError,
)

from netbox_sdk.services import (  # isort: skip
    ACTION_METHOD_MAP,
    ResolvedRequest,
    load_json_payload,
    parse_key_value_pairs,
    resolve_dynamic_request,
    run_dynamic_command,
)
