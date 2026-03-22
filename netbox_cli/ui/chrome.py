from __future__ import annotations

from datetime import datetime
from typing import Any

from rich.text import Text
from textual.css.query import NoMatches
from textual.widgets import Static

from netbox_cli.api import ConnectionProbe
from netbox_cli.theme_registry import ThemeCatalog, ThemeDefinition, load_theme_catalog

from .formatting import configure_semantic_styles
from .logo_render import build_netbox_logo

_THEME_CATALOG: ThemeCatalog | None = None


def get_theme_catalog() -> ThemeCatalog:
    global _THEME_CATALOG
    if _THEME_CATALOG is None:
        _THEME_CATALOG = load_theme_catalog()
    return _THEME_CATALOG


def initialize_theme_state(
    app: Any,
    *,
    requested_theme_name: str | None,
    persisted_theme_name: str | None,
) -> tuple[ThemeCatalog, str, tuple[tuple[str, str], ...]]:
    catalog = get_theme_catalog()
    requested_theme = catalog.resolve(requested_theme_name) if requested_theme_name else None
    state_theme = catalog.resolve(persisted_theme_name)
    theme_name = requested_theme or state_theme or catalog.default_theme_name
    theme_options = catalog.select_options()
    active_definition = catalog.theme_for(theme_name)
    configure_semantic_styles(
        colors=active_definition.colors,
        variables=active_definition.variables,
    )
    for definition in catalog.themes:
        app.register_theme(definition.to_textual_theme())
    app.theme = theme_name
    return catalog, theme_name, theme_options


def apply_theme(
    app: Any,
    *,
    theme_catalog: ThemeCatalog,
    theme_options: tuple[tuple[str, str], ...],
    current_theme_name: str,
    new_theme_name: str,
    state: Any,
    logo_widget_id: str,
    notify: bool = False,
) -> str:
    definition = theme_catalog.theme_for(new_theme_name)
    configure_semantic_styles(colors=definition.colors, variables=definition.variables)

    if current_theme_name:
        app.screen.remove_class(f"theme-{current_theme_name}")
    app.theme = new_theme_name
    app.screen.add_class(f"theme-{new_theme_name}")
    state.theme_name = new_theme_name
    refresh_logo_widget(app, definition=definition, widget_id=logo_widget_id)
    if notify:
        label = next(
            (label for label, key in theme_options if key == new_theme_name),
            new_theme_name,
        )
        app.notify(f"Theme switched to {label}")
    return new_theme_name


def logo_renderable(theme_catalog: ThemeCatalog, theme_name: str) -> Text:
    return build_netbox_logo(theme_catalog.theme_for(theme_name))


def refresh_logo_widget(app: Any, *, definition: ThemeDefinition, widget_id: str) -> None:
    try:
        logo = app.query_one(widget_id, Static)
    except NoMatches:
        return
    logo.update(build_netbox_logo(definition))


def strip_theme_select_prefix(app: Any, *, selector: str) -> None:
    try:
        label = app.query_one(selector, Static)
    except NoMatches:
        return
    text = str(label.content)
    if text.startswith("- "):
        label.update(text[2:])


def update_clock_widget(app: Any, *, widget_id: str) -> None:
    try:
        app.query_one(widget_id, Static).update(datetime.now().strftime("%H:%M:%S"))
    except NoMatches:
        return


def set_connection_badge_state(app: Any, *, badge_id: str, state: str) -> None:
    badge = app.query_one(badge_id, Static)
    badge.remove_class("-checking")
    badge.remove_class("-ok")
    badge.remove_class("-warning")
    badge.remove_class("-error")
    badge.add_class(f"-{state}")
    badge.update("●")


def badge_state_for_probe(probe: ConnectionProbe) -> str:
    if probe.status == 0:
        return "error"
    if probe.ok and probe.status < 300:
        return "ok"
    if probe.ok and probe.status == 403:
        return "warning"
    return "error"
