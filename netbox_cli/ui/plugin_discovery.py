"""Re-exports from sdk.plugin_discovery — real implementation lives in the sdk package."""

from sdk.plugin_discovery import (
    PLUGIN_ROOT,
    discover_plugin_resource_paths,
)

__all__ = [
    "PLUGIN_ROOT",
    "discover_plugin_resource_paths",
]
