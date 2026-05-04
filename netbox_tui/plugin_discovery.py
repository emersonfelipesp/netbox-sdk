"""Re-exports from netbox_sdk.plugin_discovery — real implementation lives in the sdk package."""

from netbox_sdk.plugin_discovery import (
    PLUGIN_ROOT,
    DiscoveredResource,
    discover_object_type_resources,
    discover_plugin_resource_paths,
    discover_plugin_resources,
    discover_runtime_resources,
    enrich_schema_index_with_runtime_resources,
)

__all__ = [
    "DiscoveredResource",
    "PLUGIN_ROOT",
    "discover_object_type_resources",
    "discover_plugin_resource_paths",
    "discover_plugin_resources",
    "discover_runtime_resources",
    "enrich_schema_index_with_runtime_resources",
]
