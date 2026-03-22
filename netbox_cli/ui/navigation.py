from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from netbox_cli.schema import SchemaIndex

from .formatting import humanize_resource


class NavItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    group: str | None = None
    resource: str | None = None


class NavGroup(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    items: tuple[NavItem, ...]


class NavMenu(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    groups: tuple[NavGroup, ...]


# Mirror netbox/netbox/netbox/navigation/menu.py ordering.
_NAV_BLUEPRINT: tuple[
    tuple[str, tuple[tuple[str, tuple[tuple[str, str | None, str | None], ...]], ...]], ...
] = (
    (
        "Organization",
        (
            (
                "Sites",
                (
                    ("Regions", "dcim", "regions"),
                    ("Site Groups", "dcim", "site-groups"),
                    ("Sites", "dcim", "sites"),
                    ("Locations", "dcim", "locations"),
                ),
            ),
            (
                "Tenancy",
                (
                    ("Tenants", "tenancy", "tenants"),
                    ("Tenant Groups", "tenancy", "tenant-groups"),
                ),
            ),
            (
                "Contacts",
                (
                    ("Contacts", "tenancy", "contacts"),
                    ("Contact Groups", "tenancy", "contact-groups"),
                    ("Contact Roles", "tenancy", "contact-roles"),
                    ("Contact Assignments", "tenancy", "contact-assignments"),
                ),
            ),
        ),
    ),
    (
        "Racks",
        (
            (
                "Racks",
                (
                    ("Racks", "dcim", "racks"),
                    ("Rack Roles", "dcim", "rack-roles"),
                    ("Reservations", "dcim", "rack-reservations"),
                    ("Elevations", None, None),
                ),
            ),
            (
                "Rack Types",
                (("Rack Types", "dcim", "rack-types"),),
            ),
        ),
    ),
    (
        "Devices",
        (
            (
                "Devices",
                (
                    ("Devices", "dcim", "devices"),
                    ("Modules", "dcim", "modules"),
                    ("Device Roles", "dcim", "device-roles"),
                    ("Platforms", "dcim", "platforms"),
                    ("Virtual Chassis", "dcim", "virtual-chassis"),
                    ("Virtual Device Contexts", "dcim", "virtual-device-contexts"),
                ),
            ),
            (
                "Device Types",
                (
                    ("Device Types", "dcim", "device-types"),
                    ("Module Types", "dcim", "module-types"),
                    ("Module Type Profiles", "dcim", "module-type-profiles"),
                    ("Manufacturers", "dcim", "manufacturers"),
                ),
            ),
            (
                "Device Components",
                (
                    ("Interfaces", "dcim", "interfaces"),
                    ("Front Ports", "dcim", "front-ports"),
                    ("Rear Ports", "dcim", "rear-ports"),
                    ("Console Ports", "dcim", "console-ports"),
                    ("Console Server Ports", "dcim", "console-server-ports"),
                    ("Power Ports", "dcim", "power-ports"),
                    ("Power Outlets", "dcim", "power-outlets"),
                    ("Module Bays", "dcim", "module-bays"),
                    ("Device Bays", "dcim", "device-bays"),
                    ("Inventory Items", "dcim", "inventory-items"),
                    ("Inventory Item Roles", "dcim", "inventory-item-roles"),
                ),
            ),
            (
                "Addressing",
                (("MAC Addresses", "dcim", "mac-addresses"),),
            ),
        ),
    ),
    (
        "Connections",
        (
            (
                "Connections",
                (
                    ("Cables", "dcim", "cables"),
                    ("Wireless Links", "wireless", "wireless-links"),
                    ("Interface Connections", None, None),
                    ("Console Connections", None, None),
                    ("Power Connections", None, None),
                ),
            ),
        ),
    ),
    (
        "Wireless",
        (
            (
                "Wireless",
                (
                    ("Wireless LANs", "wireless", "wireless-lans"),
                    ("Wireless LAN Groups", "wireless", "wireless-lan-groups"),
                ),
            ),
        ),
    ),
    (
        "IPAM",
        (
            (
                "IP Addresses",
                (
                    ("IP Addresses", "ipam", "ip-addresses"),
                    ("IP Ranges", "ipam", "ip-ranges"),
                ),
            ),
            (
                "Prefixes",
                (
                    ("Prefixes", "ipam", "prefixes"),
                    ("Prefix & VLAN Roles", "ipam", "roles"),
                ),
            ),
            (
                "ASNs",
                (
                    ("ASN Ranges", "ipam", "asn-ranges"),
                    ("ASNs", "ipam", "asns"),
                ),
            ),
            (
                "Aggregates",
                (
                    ("Aggregates", "ipam", "aggregates"),
                    ("RIRs", "ipam", "rirs"),
                ),
            ),
            (
                "VRFs",
                (
                    ("VRFs", "ipam", "vrfs"),
                    ("Route Targets", "ipam", "route-targets"),
                ),
            ),
            (
                "VLANs",
                (
                    ("VLANs", "ipam", "vlans"),
                    ("VLAN Groups", "ipam", "vlan-groups"),
                    ("VLAN Translation Policies", "ipam", "vlan-translation-policies"),
                    ("VLAN Translation Rules", "ipam", "vlan-translation-rules"),
                ),
            ),
            (
                "Other",
                (
                    ("FHRP Groups", "ipam", "fhrp-groups"),
                    ("Application Service Templates", "ipam", "service-templates"),
                    ("Application Services", "ipam", "services"),
                ),
            ),
        ),
    ),
    (
        "VPN",
        (
            (
                "Tunnels",
                (
                    ("Tunnels", "vpn", "tunnels"),
                    ("Tunnel Groups", "vpn", "tunnel-groups"),
                    ("Tunnel Terminations", "vpn", "tunnel-terminations"),
                ),
            ),
            (
                "L2VPNs",
                (
                    ("L2VPNs", "vpn", "l2vpns"),
                    ("L2VPN Terminations", "vpn", "l2vpn-terminations"),
                ),
            ),
            (
                "Security",
                (
                    ("IKE Proposals", "vpn", "ike-proposals"),
                    ("IKE Policies", "vpn", "ike-policies"),
                    ("IPSec Proposals", "vpn", "ipsec-proposals"),
                    ("IPSec Policies", "vpn", "ipsec-policies"),
                    ("IPSec Profiles", "vpn", "ipsec-profiles"),
                ),
            ),
        ),
    ),
    (
        "Virtualization",
        (
            (
                "Virtual Machines",
                (
                    ("Virtual Machines", "virtualization", "virtual-machines"),
                    ("Interfaces", "virtualization", "interfaces"),
                    ("Virtual Disks", "virtualization", "virtual-disks"),
                ),
            ),
            (
                "Clusters",
                (
                    ("Clusters", "virtualization", "clusters"),
                    ("Cluster Types", "virtualization", "cluster-types"),
                    ("Cluster Groups", "virtualization", "cluster-groups"),
                ),
            ),
        ),
    ),
    (
        "Circuits",
        (
            (
                "Circuits",
                (
                    ("Circuits", "circuits", "circuits"),
                    ("Circuit Types", "circuits", "circuit-types"),
                    ("Circuit Terminations", "circuits", "circuit-terminations"),
                ),
            ),
            (
                "Virtual Circuits",
                (
                    ("Virtual Circuits", "circuits", "virtual-circuits"),
                    ("Virtual Circuit Types", "circuits", "virtual-circuit-types"),
                    ("Virtual Circuit Terminations", "circuits", "virtual-circuit-terminations"),
                ),
            ),
            (
                "Groups",
                (
                    ("Circuit Groups", "circuits", "circuit-groups"),
                    ("Group Assignments", "circuits", "circuit-group-assignments"),
                ),
            ),
            (
                "Providers",
                (
                    ("Providers", "circuits", "providers"),
                    ("Provider Accounts", "circuits", "provider-accounts"),
                    ("Provider Networks", "circuits", "provider-networks"),
                ),
            ),
        ),
    ),
    (
        "Power",
        (
            (
                "Power",
                (
                    ("Power Feeds", "dcim", "power-feeds"),
                    ("Power Panels", "dcim", "power-panels"),
                ),
            ),
        ),
    ),
    (
        "Provisioning",
        (
            (
                "Configurations",
                (
                    ("Config Contexts", "extras", "config-contexts"),
                    ("Config Context Profiles", "extras", "config-context-profiles"),
                    ("Config Templates", "extras", "config-templates"),
                ),
            ),
        ),
    ),
    (
        "Customization",
        (
            (
                "Customization",
                (
                    ("Custom Fields", "extras", "custom-fields"),
                    ("Custom Field Choices", "extras", "custom-field-choice-sets"),
                    ("Custom Links", "extras", "custom-links"),
                    ("Export Templates", "extras", "export-templates"),
                    ("Saved Filters", "extras", "saved-filters"),
                    ("Table Configs", "extras", "table-configs"),
                    ("Tags", "extras", "tags"),
                    ("Image Attachments", "extras", "image-attachments"),
                ),
            ),
            (
                "Scripts",
                (("Scripts", "extras", "scripts"),),
            ),
        ),
    ),
    (
        "Operations",
        (
            (
                "Integrations",
                (
                    ("Data Sources", "core", "data-sources"),
                    ("Event Rules", "extras", "event-rules"),
                    ("Webhooks", "extras", "webhooks"),
                ),
            ),
            (
                "Jobs",
                (("Jobs", "core", "jobs"),),
            ),
            (
                "Logging",
                (
                    ("Notification Groups", "extras", "notification-groups"),
                    ("Journal Entries", "extras", "journal-entries"),
                    ("Change Log", "core", "object-changes"),
                ),
            ),
        ),
    ),
    (
        "Admin",
        (
            (
                "Authentication",
                (
                    ("Users", "users", "users"),
                    ("Groups", "users", "groups"),
                    ("API Tokens", "users", "tokens"),
                    ("Permissions", "users", "permissions"),
                ),
            ),
            (
                "Ownership",
                (
                    ("Owner Groups", "users", "owner-groups"),
                    ("Owners", "users", "owners"),
                ),
            ),
            (
                "System",
                (
                    ("System", None, None),
                    ("Plugins", None, None),
                    ("Configuration History", None, None),
                    ("Background Tasks", "core", "background-queues"),
                ),
            ),
        ),
    ),
)


def _plugin_menu(index: SchemaIndex) -> NavMenu | None:
    if "plugins" not in index.groups():
        return None

    items = tuple(
        NavItem(label=humanize_resource(resource), group="plugins", resource=resource)
        for resource in index.resources("plugins")
    )
    if not items:
        return None

    return NavMenu(label="Plugins", groups=(NavGroup(label="Plugins", items=items),))


def build_navigation_menus(index: SchemaIndex) -> list[NavMenu]:
    available = {
        (group, resource) for group in index.groups() for resource in index.resources(group)
    }

    menus: list[NavMenu] = []
    for menu_label, group_specs in _NAV_BLUEPRINT:
        menu_groups: list[NavGroup] = []
        for group_label, item_specs in group_specs:
            group_items: list[NavItem] = []
            for item_label, group, resource in item_specs:
                if group is None or resource is None:
                    group_items.append(NavItem(label=item_label))
                    continue
                if (group, resource) not in available:
                    # Keep order and visibility consistent with NetBox menu labels.
                    group_items.append(NavItem(label=item_label))
                    continue
                group_items.append(NavItem(label=item_label, group=group, resource=resource))
            if group_items:
                menu_groups.append(NavGroup(label=group_label, items=tuple(group_items)))
        if menu_groups:
            menus.append(NavMenu(label=menu_label, groups=tuple(menu_groups)))

    plugins_menu = _plugin_menu(index)
    if plugins_menu is not None:
        # NetBox appends plugin menus before admin. Keep admin last.
        admin_menu = menus.pop() if menus and menus[-1].label == "Admin" else None
        menus.append(plugins_menu)
        if admin_menu is not None:
            menus.append(admin_menu)

    return menus
