"""First-class plugin support declarations.

Unknown plugins remain reachable through runtime discovery.  This registry only
identifies plugins whose workflow semantics have a maintained SDK/CLI surface.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OfficialPlugin(BaseModel):
    """A NetBox plugin with a maintained first-class SDK contract."""

    model_config = ConfigDict(frozen=True)

    package: str
    api_slug: str
    sdk_module: str
    cli_command: str
    description: str


OFFICIAL_PLUGINS: tuple[OfficialPlugin, ...] = (
    OfficialPlugin(
        package="netbox-openbao",
        api_slug="openbao",
        sdk_module="netbox_sdk.openbao",
        cli_command="openbao",
        description="Credential lifecycle and reviewed OpenBao administration workflows.",
    ),
    OfficialPlugin(
        package="netbox-rpc",
        api_slug="rpc",
        sdk_module="netbox_sdk.rpc",
        cli_command="rpc",
        description="Audited procedure catalog and execution lifecycle.",
    ),
    OfficialPlugin(
        package="netbox-proxbox",
        api_slug="proxbox",
        sdk_module="netbox_sdk.proxbox",
        cli_command="proxbox",
        description="Proxmox inventory, synchronization, and operational workflows.",
    ),
)


def official_plugins() -> tuple[OfficialPlugin, ...]:
    """Return the immutable first-class plugin registry."""
    return OFFICIAL_PLUGINS


def official_plugin(value: str) -> OfficialPlugin | None:
    """Resolve a package name, API slug, or CLI command."""
    normalized = value.strip().casefold().replace("_", "-")
    for plugin in OFFICIAL_PLUGINS:
        aliases = {
            plugin.package.casefold(),
            plugin.api_slug.casefold().replace("_", "-"),
            plugin.cli_command.casefold().replace("_", "-"),
        }
        if normalized in aliases:
            return plugin
    return None


__all__ = ["OFFICIAL_PLUGINS", "OfficialPlugin", "official_plugin", "official_plugins"]
