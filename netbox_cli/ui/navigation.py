"""Navigation menu structure for the NetBox TUI.

``build_navigation_menus`` converts the static ``NAV_BLUEPRINT`` (imported from
``nav_blueprint``) into typed ``NavMenu`` / ``NavGroup`` / ``NavItem`` objects,
filtering each entry against the live ``SchemaIndex`` so that resources missing
from the connected NetBox instance are rendered as non-navigable labels instead
of being hidden entirely — preserving menu structure parity with the NetBox UI.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from netbox_cli.schema import SchemaIndex

from .formatting import humanize_resource
from .nav_blueprint import NAV_BLUEPRINT


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


def _plugin_menu(index: SchemaIndex) -> NavMenu | None:
    if "plugins" not in index.groups():
        return None

    grouped: dict[str, list[NavItem]] = {}
    for resource in index.resources("plugins"):
        plugin_name, _, plugin_resource = resource.partition("/")
        label = humanize_resource(plugin_resource or resource)
        grouped.setdefault(plugin_name, []).append(
            NavItem(label=label, group="plugins", resource=resource)
        )

    if not grouped:
        return None

    groups = tuple(
        NavGroup(
            label=humanize_resource(plugin_name),
            items=tuple(sorted(items, key=lambda item: item.label)),
        )
        for plugin_name, items in sorted(grouped.items())
    )
    return NavMenu(label="Plugins", groups=groups)


def build_navigation_menus(index: SchemaIndex) -> list[NavMenu]:
    available = {
        (group, resource) for group in index.groups() for resource in index.resources(group)
    }

    menus: list[NavMenu] = []
    for menu_label, group_specs in NAV_BLUEPRINT:
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
