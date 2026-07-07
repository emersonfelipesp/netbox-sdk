"""Proxbox-focused Textual request workbench."""

from __future__ import annotations

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.proxbox import build_proxbox_schema_index
from netbox_tui.chrome import get_theme_catalog
from netbox_tui.dev_app import NetBoxDevTuiApp


def available_theme_names() -> tuple[str, ...]:
    return get_theme_catalog().available_theme_names()


def resolve_theme_name(theme_name: str | None) -> str | None:
    return get_theme_catalog().resolve(theme_name)


def build_proxbox_tui_app(
    *,
    client: NetBoxApiClient,
    theme_name: str | None = None,
) -> NetBoxDevTuiApp:
    """Return the Proxbox-only request workbench app."""
    return NetBoxDevTuiApp(
        client=client,
        index=build_proxbox_schema_index(),
        theme_name=theme_name,
        discard_plugin_resources=False,
        discover_plugin_resources=False,
        title="NetBox Proxbox",
        subtitle="Dedicated netbox-proxbox request workbench",
        sidebar_title="Proxbox Resources",
        idle_summary="Choose a Proxbox resource from the left sidebar to load its operations.",
    )


def run_proxbox_tui(
    *,
    client: NetBoxApiClient,
    theme_name: str | None = None,
) -> None:
    try:
        app = build_proxbox_tui_app(client=client, theme_name=theme_name)
        app.run()
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception as exc:  # noqa: BLE001
        detail = str(exc).strip() or exc.__class__.__name__
        raise RuntimeError(f"Unable to launch the Proxbox TUI: {detail}") from None


__all__ = [
    "available_theme_names",
    "build_proxbox_tui_app",
    "resolve_theme_name",
    "run_proxbox_tui",
]
