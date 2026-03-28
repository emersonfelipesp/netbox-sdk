"""netbox-cli / netbox-sdk — async NetBox API client, schema index, and service helpers."""

from __future__ import annotations

from .api import ApiResponse, ConnectionProbe, NetBoxApiClient, RequestError
from .config import Config, load_profile_config, save_config
from .schema import SchemaIndex, load_openapi_schema
from .services import ResolvedRequest, resolve_dynamic_request, run_dynamic_command

__all__ = [
    "__version__",
    "ApiResponse",
    "Config",
    "ConnectionProbe",
    "NetBoxApiClient",
    "RequestError",
    "ResolvedRequest",
    "SchemaIndex",
    "load_openapi_schema",
    "load_profile_config",
    "resolve_dynamic_request",
    "run_dynamic_command",
    "save_config",
]

__version__ = "0.0.4"
