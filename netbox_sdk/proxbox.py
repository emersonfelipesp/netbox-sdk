"""netbox-proxbox resource catalog and SDK helpers.

The generic plugin discovery path remains the preferred zero-config behavior for
unknown NetBox plugins. This module adds a stable operator-facing catalog for
netbox-proxbox so CLI and TUI surfaces can be registered without a live schema
probe at import time.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict

from netbox_sdk.client import ApiResponse, NetBoxApiClient
from netbox_sdk.http_cache import QueryParams
from netbox_sdk.schema import SchemaIndex, parse_group_resource
from netbox_sdk.services import resolve_dynamic_request


class ProxboxResourceSpec(BaseModel):
    """One REST resource exposed by the netbox-proxbox plugin."""

    model_config = ConfigDict(frozen=True)

    key: str
    command_parts: tuple[str, ...]
    label: str
    category: str
    description: str
    list_path: str
    detail_path: str | None = None
    list_methods: tuple[str, ...] = ("GET",)
    detail_methods: tuple[str, ...] = ("GET",)

    @property
    def resource(self) -> str:
        """Return the ``SchemaIndex`` plugin resource name."""
        group, resource = parse_group_resource(self.list_path)
        if group != "plugins" or resource is None:
            raise ValueError(f"Invalid Proxbox plugin list path: {self.list_path}")
        return resource

    @property
    def command_path(self) -> str:
        return "/".join(self.command_parts)

    @property
    def read_only(self) -> bool:
        return not any(
            action in {"create", "update", "patch", "delete"}
            for action in self.supported_actions
        )

    @property
    def supported_actions(self) -> tuple[str, ...]:
        actions: list[str] = []
        list_methods = {method.upper() for method in self.list_methods}
        detail_methods = {method.upper() for method in self.detail_methods}
        if "GET" in list_methods:
            actions.append("list")
        if self.detail_path and "GET" in detail_methods:
            actions.append("get")
        if "POST" in list_methods:
            actions.append("create")
        if self.detail_path and "PUT" in detail_methods:
            actions.append("update")
        if self.detail_path and "PATCH" in detail_methods:
            actions.append("patch")
        if self.detail_path and "DELETE" in detail_methods:
            actions.append("delete")
        return tuple(actions)


def _model_resource(
    key: str,
    command_parts: tuple[str, ...],
    label: str,
    category: str,
    description: str,
    path: str,
) -> ProxboxResourceSpec:
    return ProxboxResourceSpec(
        key=key,
        command_parts=command_parts,
        label=label,
        category=category,
        description=description,
        list_path=f"/api/plugins/proxbox/{path}/",
        detail_path=f"/api/plugins/proxbox/{path}/{{id}}/",
        list_methods=("GET", "POST"),
        detail_methods=("GET", "PUT", "PATCH", "DELETE"),
    )


PROXBOX_RESOURCES: tuple[ProxboxResourceSpec, ...] = (
    _model_resource(
        "endpoints/proxmox",
        ("endpoints", "proxmox"),
        "Proxmox endpoints",
        "Endpoints",
        "Proxmox API connection records used by sync and operational workflows.",
        "endpoints/proxmox",
    ),
    _model_resource(
        "endpoints/netbox",
        ("endpoints", "netbox"),
        "NetBox endpoints",
        "Endpoints",
        "Remote NetBox endpoint records used by Proxbox integrations.",
        "endpoints/netbox",
    ),
    _model_resource(
        "endpoints/fastapi",
        ("endpoints", "fastapi"),
        "FastAPI endpoints",
        "Endpoints",
        "proxbox-api backend connection records.",
        "endpoints/fastapi",
    ),
    _model_resource(
        "endpoints/pbs",
        ("endpoints", "pbs"),
        "PBS endpoints",
        "Endpoints",
        "Proxmox Backup Server endpoint records.",
        "endpoints/pbs",
    ),
    _model_resource(
        "endpoints/pdm",
        ("endpoints", "pdm"),
        "PDM endpoints",
        "Endpoints",
        "Proxmox Datacenter Manager endpoint records.",
        "endpoints/pdm",
    ),
    _model_resource(
        "proxmox-clusters",
        ("inventory", "clusters"),
        "Proxmox clusters",
        "Inventory",
        "Cluster inventory synchronized from Proxmox.",
        "proxmox-clusters",
    ),
    _model_resource(
        "proxmox-nodes",
        ("inventory", "nodes"),
        "Proxmox nodes",
        "Inventory",
        "Node inventory synchronized from Proxmox.",
        "proxmox-nodes",
    ),
    _model_resource(
        "storage",
        ("inventory", "storage"),
        "Proxmox storage",
        "Inventory",
        "Storage pools and backends synchronized from Proxmox.",
        "storage",
    ),
    _model_resource(
        "cloud-image-templates",
        ("images", "cloud-templates"),
        "Cloud image templates",
        "Images",
        "Cloud image template records used by Proxbox provisioning flows.",
        "cloud-image-templates",
    ),
    _model_resource(
        "vm-templates",
        ("virtual-machines", "templates"),
        "Proxmox VM templates",
        "Virtual Machines",
        "Proxmox VM template catalog rows.",
        "vm-templates",
    ),
    _model_resource(
        "vm-cloudinit",
        ("virtual-machines", "cloudinit"),
        "VM cloud-init",
        "Virtual Machines",
        "Cloud-init metadata stored for Proxmox virtual machines.",
        "vm-cloudinit",
    ),
    _model_resource(
        "backups",
        ("operations", "backups"),
        "VM backups",
        "Operations",
        "Backup artifacts synchronized from Proxmox/PBS.",
        "backups",
    ),
    _model_resource(
        "backup-routines",
        ("operations", "backup-routines"),
        "Backup routines",
        "Operations",
        "Scheduled Proxmox backup jobs.",
        "backup-routines",
    ),
    _model_resource(
        "replications",
        ("operations", "replications"),
        "Replications",
        "Operations",
        "Proxmox replication jobs.",
        "replications",
    ),
    _model_resource(
        "snapshots",
        ("operations", "snapshots"),
        "VM snapshots",
        "Operations",
        "Snapshot records synchronized from Proxmox.",
        "snapshots",
    ),
    _model_resource(
        "task-history",
        ("operations", "task-history"),
        "Task history",
        "Operations",
        "Proxmox task history rows.",
        "task-history",
    ),
    _model_resource(
        "ssh-credentials",
        ("access", "ssh-credentials"),
        "Node SSH credentials",
        "Access",
        "Stored SSH credential metadata for terminal workflows.",
        "ssh-credentials",
    ),
    _model_resource(
        "firecracker-host-pools",
        ("firecracker", "host-pools"),
        "Firecracker host pools",
        "Firecracker",
        "NMS Cloud Firecracker host-pool inventory.",
        "firecracker-host-pools",
    ),
    _model_resource(
        "firecracker-hosts",
        ("firecracker", "hosts"),
        "Firecracker hosts",
        "Firecracker",
        "NMS Cloud Firecracker host inventory.",
        "firecracker-hosts",
    ),
    _model_resource(
        "firecracker-image-templates",
        ("firecracker", "image-templates"),
        "Firecracker image templates",
        "Firecracker",
        "Firecracker image template catalog.",
        "firecracker-image-templates",
    ),
    _model_resource(
        "firecracker-microvms",
        ("firecracker", "microvms"),
        "Firecracker micro-VMs",
        "Firecracker",
        "Firecracker micro-VM inventory rows.",
        "firecracker-microvms",
    ),
    _model_resource(
        "firewall/security-groups",
        ("firewall", "security-groups"),
        "Firewall security groups",
        "Firewall",
        "Proxmox firewall security group rows.",
        "firewall/security-groups",
    ),
    _model_resource(
        "firewall/rules",
        ("firewall", "rules"),
        "Firewall rules",
        "Firewall",
        "Proxmox firewall rule rows.",
        "firewall/rules",
    ),
    _model_resource(
        "firewall/ipsets",
        ("firewall", "ipsets"),
        "Firewall IP sets",
        "Firewall",
        "Proxmox firewall IP set rows.",
        "firewall/ipsets",
    ),
    _model_resource(
        "firewall/ipset-entries",
        ("firewall", "ipset-entries"),
        "Firewall IP set entries",
        "Firewall",
        "Proxmox firewall IP set entry rows.",
        "firewall/ipset-entries",
    ),
    _model_resource(
        "firewall/aliases",
        ("firewall", "aliases"),
        "Firewall aliases",
        "Firewall",
        "Proxmox firewall alias rows.",
        "firewall/aliases",
    ),
    _model_resource(
        "firewall/options",
        ("firewall", "options"),
        "Firewall options",
        "Firewall",
        "Proxmox firewall option rows.",
        "firewall/options",
    ),
    _model_resource(
        "sdn-fabrics",
        ("sdn", "fabrics"),
        "SDN fabrics",
        "SDN",
        "Proxmox SDN fabric records.",
        "sdn-fabrics",
    ),
    _model_resource(
        "sdn-controllers",
        ("sdn", "controllers"),
        "SDN controllers",
        "SDN",
        "Proxmox SDN controller records.",
        "sdn-controllers",
    ),
    _model_resource(
        "sdn-zones",
        ("sdn", "zones"),
        "SDN zones",
        "SDN",
        "Proxmox SDN zone records.",
        "sdn-zones",
    ),
    _model_resource(
        "sdn-vnets",
        ("sdn", "vnets"),
        "SDN VNets",
        "SDN",
        "Proxmox SDN VNet records.",
        "sdn-vnets",
    ),
    _model_resource(
        "sdn-subnets",
        ("sdn", "subnets"),
        "SDN subnets",
        "SDN",
        "Proxmox SDN subnet records.",
        "sdn-subnets",
    ),
    _model_resource(
        "sdn-bindings",
        ("sdn", "bindings"),
        "SDN bindings",
        "SDN",
        "Proxmox SDN binding records.",
        "sdn-bindings",
    ),
    _model_resource(
        "sdn-route-maps",
        ("sdn", "route-maps"),
        "SDN route maps",
        "SDN",
        "Proxmox SDN route-map records.",
        "sdn-route-maps",
    ),
    _model_resource(
        "sdn-prefix-lists",
        ("sdn", "prefix-lists"),
        "SDN prefix lists",
        "SDN",
        "Proxmox SDN prefix-list records.",
        "sdn-prefix-lists",
    ),
    _model_resource(
        "datacenter-cpu-models",
        ("datacenter", "cpu-models"),
        "Datacenter CPU models",
        "Datacenter",
        "Allowed datacenter CPU model records.",
        "datacenter-cpu-models",
    ),
    _model_resource(
        "pdm-remotes",
        ("pdm", "remotes"),
        "PDM remotes",
        "PDM",
        "Proxmox Datacenter Manager remote records.",
        "pdm-remotes",
    ),
    ProxboxResourceSpec(
        key="settings",
        command_parts=("settings",),
        label="Plugin settings",
        category="Settings",
        description="Singleton netbox-proxbox runtime settings. PATCH the detail row to update.",
        list_path="/api/plugins/proxbox/settings/",
        detail_path="/api/plugins/proxbox/settings/{id}/",
        list_methods=("GET",),
        detail_methods=("GET", "PATCH"),
    ),
    ProxboxResourceSpec(
        key="deletion-requests",
        command_parts=("operations", "deletion-requests"),
        label="Deletion requests",
        category="Operations",
        description="Read-only deletion approval queue; writes are blocked by Proxbox safety policy.",
        list_path="/api/plugins/proxbox/deletion-requests/",
        detail_path="/api/plugins/proxbox/deletion-requests/{id}/",
        list_methods=("GET",),
        detail_methods=("GET",),
    ),
    ProxboxResourceSpec(
        key="apply-jobs",
        command_parts=("operations", "apply-jobs"),
        label="Apply jobs",
        category="Operations",
        description="Read-only intent apply audit records written by backend workflows.",
        list_path="/api/plugins/proxbox/apply-jobs/",
        detail_path="/api/plugins/proxbox/apply-jobs/{id}/",
        list_methods=("GET",),
        detail_methods=("GET",),
    ),
    ProxboxResourceSpec(
        key="home",
        command_parts=("views", "home"),
        label="Home summary",
        category="Views",
        description="JSON mirror of the Proxbox home page.",
        list_path="/api/plugins/proxbox/home/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="dashboard",
        command_parts=("views", "dashboard"),
        label="Dashboard",
        category="Views",
        description="JSON mirror of the Proxbox dashboard.",
        list_path="/api/plugins/proxbox/dashboard/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="logs",
        command_parts=("views", "logs"),
        label="Backend logs",
        category="Views",
        description="Backend log view exposed by the plugin API.",
        list_path="/api/plugins/proxbox/logs/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="ha/summary",
        command_parts=("views", "ha-summary"),
        label="HA summary",
        category="Views",
        description="Cluster HA summary proxy.",
        list_path="/api/plugins/proxbox/ha/summary/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/clusters",
        command_parts=("resource-views", "clusters"),
        label="Cluster resource view",
        category="Resource Views",
        description="Aggregated cluster resource list.",
        list_path="/api/plugins/proxbox/resources/clusters/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/nodes",
        command_parts=("resource-views", "nodes"),
        label="Node resource view",
        category="Resource Views",
        description="Aggregated node resource list.",
        list_path="/api/plugins/proxbox/resources/nodes/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/virtual-machines",
        command_parts=("resource-views", "virtual-machines"),
        label="Virtual machine resource view",
        category="Resource Views",
        description="Aggregated VM resource list.",
        list_path="/api/plugins/proxbox/resources/virtual-machines/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/lxc-containers",
        command_parts=("resource-views", "lxc-containers"),
        label="LXC resource view",
        category="Resource Views",
        description="Aggregated LXC container resource list.",
        list_path="/api/plugins/proxbox/resources/lxc-containers/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/firecracker-microvms",
        command_parts=("resource-views", "firecracker-microvms"),
        label="Firecracker micro-VM resource view",
        category="Resource Views",
        description="NMS-compatible Firecracker micro-VM list.",
        list_path="/api/plugins/proxbox/resources/firecracker-microvms/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/interfaces",
        command_parts=("resource-views", "interfaces"),
        label="Interface resource view",
        category="Resource Views",
        description="Aggregated VM interface list.",
        list_path="/api/plugins/proxbox/resources/interfaces/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/ip-addresses",
        command_parts=("resource-views", "ip-addresses"),
        label="IP address resource view",
        category="Resource Views",
        description="Aggregated IP address list.",
        list_path="/api/plugins/proxbox/resources/ip-addresses/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="resources/virtual-disks",
        command_parts=("resource-views", "virtual-disks"),
        label="Virtual disk resource view",
        category="Resource Views",
        description="Aggregated virtual disk list.",
        list_path="/api/plugins/proxbox/resources/virtual-disks/",
        list_methods=("GET",),
        detail_methods=(),
    ),
    ProxboxResourceSpec(
        key="sync/schedule",
        command_parts=("schedule",),
        label="Schedule sync",
        category="Operations",
        description="Low-level schedule endpoint. Prefer `nbx proxbox sync` for guided streaming.",
        list_path="/api/plugins/proxbox/sync/schedule/",
        list_methods=("GET", "POST"),
        detail_methods=(),
    ),
)

_BY_KEY: dict[str, ProxboxResourceSpec] = {spec.key: spec for spec in PROXBOX_RESOURCES}
_BY_COMMAND_PATH: dict[str, ProxboxResourceSpec] = {
    spec.command_path: spec for spec in PROXBOX_RESOURCES
}
_BY_RESOURCE: dict[str, ProxboxResourceSpec] = {spec.resource: spec for spec in PROXBOX_RESOURCES}


def proxbox_resources() -> tuple[ProxboxResourceSpec, ...]:
    """Return the supported netbox-proxbox resource catalog."""
    return PROXBOX_RESOURCES


def find_proxbox_resource(identifier: str) -> ProxboxResourceSpec:
    """Resolve a Proxbox resource by catalog key, command path, API resource, or list path."""
    normalized = identifier.strip().strip("/")
    for candidates in (_BY_KEY, _BY_COMMAND_PATH, _BY_RESOURCE):
        spec = candidates.get(normalized)
        if spec is not None:
            return spec
    for spec in PROXBOX_RESOURCES:
        if spec.list_path.strip("/") == normalized or (
            spec.detail_path and spec.detail_path.strip("/") == normalized
        ):
            return spec
    available = ", ".join(spec.command_path for spec in PROXBOX_RESOURCES)
    raise KeyError(f"Unknown Proxbox resource {identifier!r}. Available: {available}")


def register_proxbox_resources(
    index: SchemaIndex,
    resources: Iterable[ProxboxResourceSpec] = PROXBOX_RESOURCES,
) -> bool:
    """Add the Proxbox catalog to a mutable ``SchemaIndex``."""
    changed = False
    for spec in resources:
        changed = (
            index.add_discovered_resource(
                group="plugins",
                resource=spec.resource,
                list_path=spec.list_path,
                detail_path=spec.detail_path,
                list_methods=spec.list_methods,
                detail_methods=spec.detail_methods,
            )
            or changed
        )
    return changed


def build_proxbox_schema_index() -> SchemaIndex:
    """Return a fresh schema index containing only the Proxbox catalog."""
    index = SchemaIndex({"openapi": "3.0.0", "paths": {}})
    register_proxbox_resources(index)
    return index


class ProxboxResourceClient:
    """Small SDK wrapper for catalog-backed Proxbox REST requests."""

    def __init__(
        self,
        client: NetBoxApiClient,
        *,
        index: SchemaIndex | None = None,
    ) -> None:
        self.client = client
        self.index = index or build_proxbox_schema_index()

    @classmethod
    def from_client(cls, client: NetBoxApiClient) -> ProxboxResourceClient:
        return cls(client)

    async def request(
        self,
        resource: str,
        action: str,
        *,
        object_id: int | None = None,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        spec = find_proxbox_resource(resource)
        action_lower = action.lower()
        if action_lower not in spec.supported_actions:
            available = ", ".join(spec.supported_actions)
            raise ValueError(
                f"Action {action!r} is not supported for Proxbox resource "
                f"{spec.command_path!r}. Available: {available}"
            )
        resolved = resolve_dynamic_request(
            self.index,
            "plugins",
            spec.resource,
            action_lower,
            object_id=object_id,
            query=query or {},
            payload=payload,
        )
        request_kwargs: dict[str, Any] = {"query": resolved.query, "payload": resolved.payload}
        if headers:
            request_kwargs["headers"] = headers
        return await self.client.request(resolved.method, resolved.path, **request_kwargs)


__all__ = [
    "PROXBOX_RESOURCES",
    "ProxboxResourceClient",
    "ProxboxResourceSpec",
    "build_proxbox_schema_index",
    "find_proxbox_resource",
    "proxbox_resources",
    "register_proxbox_resources",
]
