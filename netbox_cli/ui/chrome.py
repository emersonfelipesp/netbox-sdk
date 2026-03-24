"""Shared top-level UI helpers for themes, clocks, badges, and logo refresh behavior."""

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
SWITCH_TO_MAIN_TUI = "switch-to-main-tui"
SWITCH_TO_DEV_TUI = "switch-to-dev-tui"
SWITCH_TO_CLI_TUI = "switch-to-cli-tui"
SWITCH_TO_DJANGO_TUI = "switch-to-django-tui"


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

    app.theme = new_theme_name
    _sync_screen_theme_classes(
        app,
        current_theme_name=current_theme_name,
        new_theme_name=new_theme_name,
    )
    app.refresh_css(animate=False)
    app.refresh(repaint=True, layout=True)
    _refresh_theme_bound_widgets(app)
    state.theme_name = new_theme_name
    refresh_logo_widget(app, definition=definition, widget_id=logo_widget_id)
    if notify:
        label = next(
            (label for label, key in theme_options if key == new_theme_name),
            new_theme_name,
        )
        app.notify(f"Theme switched to {label}")
    return new_theme_name


def _refresh_theme_bound_widgets(app: Any) -> None:
    """Repaint widgets that combine TCSS with Rich styles so theme switches fully apply."""
    for selector in (
        "#results_table",
        "#detail_table",
        "#nav_tree",
        "#global_search",
        "#active_filters",
        # Django Model Inspector TUI widgets
        "#dm_diagram",
        "#dm_source_code",
        "#dm_fields",
        "#dm_stats",
    ):
        try:
            app.query_one(selector).refresh(repaint=True, layout=False)
        except NoMatches:
            continue


def _sync_screen_theme_classes(
    app: Any,
    *,
    current_theme_name: str | None,
    new_theme_name: str,
) -> None:
    seen: set[int] = set()
    for screen in getattr(app, "screen_stack", ()):
        identity = id(screen)
        if identity in seen:
            continue
        seen.add(identity)
        if current_theme_name:
            screen.remove_class(f"theme-{current_theme_name}")
        screen.add_class(f"theme-{new_theme_name}")


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
