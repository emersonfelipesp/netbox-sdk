"""Interactive TLS verification prompts for Textual TUIs (mirrors CLI behavior)."""

from __future__ import annotations

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from netbox_sdk.client import ConnectionProbe, NetBoxApiClient
from netbox_sdk.config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    save_profile_config,
)
from netbox_sdk.http_ssl import is_certificate_verify_failure_text
from netbox_tui.widgets import NbxButton


def profile_for_netbox_client(client: NetBoxApiClient, *, demo_mode: bool = False) -> str:
    if demo_mode or client.config.base_url == DEMO_BASE_URL:
        return DEMO_PROFILE
    return DEFAULT_PROFILE


def should_offer_ssl_verify_prompt(probe: ConnectionProbe, client: NetBoxApiClient) -> bool:
    if probe.ok or client.config.ssl_verify is not None:
        return False
    return is_certificate_verify_failure_text(probe.error)


def persist_ssl_verify_choice(client: NetBoxApiClient, profile: str, *, disable: bool) -> None:
    client.config.ssl_verify = False if disable else True
    save_profile_config(profile, client.config)
    try:
        from netbox_cli.runtime import _cache_profile

        _cache_profile(profile, client.config)
    except Exception:
        pass


class SslVerifyModal(ModalScreen[str | None]):
    """Ask whether to disable TLS verification or keep it enabled (saved to config)."""

    BINDINGS = [
        Binding("escape", "keep_verification", "Cancel", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="ssl_verify_modal_dialog"):
            yield Static("TLS certificate verification failed", id="ssl_verify_modal_title")
            yield Static(
                "The server may use a self-signed or untrusted certificate. "
                "Disable verification (insecure, saved to config) or keep verification and fix the certificate or CA.",
                id="ssl_verify_modal_copy",
            )
            with Horizontal(id="ssl_verify_modal_actions"):
                yield NbxButton(
                    "Keep verification",
                    id="ssl_verify_keep",
                    size="small",
                    tone="muted",
                )
                yield NbxButton(
                    "Disable verification",
                    id="ssl_verify_disable",
                    size="small",
                    tone="warning",
                )

    def on_mount(self) -> None:
        theme_name = str(getattr(self.app, "theme_name", "") or getattr(self.app, "theme", ""))
        if theme_name:
            for class_name in tuple(self.classes):
                if class_name.startswith("theme-"):
                    self.remove_class(class_name)
            self.add_class(f"theme-{theme_name}")
        self._apply_runtime_theme_tokens()
        self.query_one("#ssl_verify_keep", Button).focus()

    def _apply_runtime_theme_tokens(self) -> None:
        theme_catalog = getattr(self.app, "theme_catalog", None)
        theme_name = str(getattr(self.app, "theme_name", "") or "")
        if not theme_catalog or not theme_name:
            return
        theme = theme_catalog.theme_for(theme_name)
        surface = theme.colors["surface"]
        panel = theme.colors["panel"]
        primary = theme.colors["primary"]
        border = theme.variables["nb-border-subtle"]
        muted = theme.variables["nb-muted-text"]

        self.set_styles(f"background: {theme.colors['background']} 65%;")
        self.query_one("#ssl_verify_modal_dialog", Vertical).set_styles(
            f"background: {surface}; border: tall {border};"
        )
        self.query_one("#ssl_verify_modal_actions", Horizontal).set_styles(
            "background: transparent; background-tint: transparent;"
        )
        self.query_one("#ssl_verify_disable", Button).set_styles(
            f"background: {panel}; color: {primary}; border: round {primary}; "
            "tint: transparent; background-tint: transparent;"
        )
        self.query_one("#ssl_verify_keep", Button).set_styles(
            f"background: transparent; color: {muted}; "
            f"border: round {border}; tint: transparent; background-tint: transparent;"
        )

    def action_keep_verification(self) -> None:
        self.dismiss("keep")

    @on(Button.Pressed, "#ssl_verify_keep")
    def keep_pressed(self) -> None:
        self.dismiss("keep")

    @on(Button.Pressed, "#ssl_verify_disable")
    def disable_pressed(self) -> None:
        self.dismiss("disable")


async def maybe_resolve_ssl_verify_interactive(
    app: App,
    client: NetBoxApiClient,
    probe: ConnectionProbe,
    *,
    demo_mode: bool = False,
) -> ConnectionProbe:
    """Show modal when appropriate; persist choice and optionally re-probe."""
    if not should_offer_ssl_verify_prompt(probe, client):
        return probe
    profile = profile_for_netbox_client(client, demo_mode=demo_mode)
    result = await app.push_screen_wait(SslVerifyModal())
    if result == "disable":
        persist_ssl_verify_choice(client, profile, disable=True)
        return await client.probe_connection()
    persist_ssl_verify_choice(client, profile, disable=False)
    return probe
