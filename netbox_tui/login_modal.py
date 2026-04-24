"""Login modal for TUI — username/password credential entry via NetBox token provisioning."""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static

from netbox_tui.widgets import NbxButton


class LoginModal(ModalScreen[bool]):
    """Username + password sign-in form that provisions a NetBox API token.

    Dismissed with ``True`` on success, ``False`` on cancel.
    On success ``self.app.client.config.token_secret`` holds the provisioned token.
    """

    BINDINGS = [Binding("escape", "cancel_login", "Cancel", show=False)]

    def compose(self) -> ComposeResult:
        need_url = not (getattr(self.app.client.config, "base_url", None) or "").strip()
        with Vertical(id="login_modal_dialog"):
            yield Static("Sign in to NetBox", id="login_modal_title")
            if need_url:
                yield Input(placeholder="https://netbox.example.com", id="login_url")
            yield Input(placeholder="Username", id="login_username")
            yield Input(placeholder="Password", password=True, id="login_password")
            yield Static("", id="login_error", markup=False)
            with Horizontal(id="login_modal_actions"):
                yield NbxButton("Cancel", id="login_cancel", size="small", tone="muted")
                yield NbxButton("Sign in", id="login_submit", size="small", tone="primary")

    def on_mount(self) -> None:
        theme_name = str(getattr(self.app, "theme_name", "") or getattr(self.app, "theme", ""))
        if theme_name:
            for class_name in tuple(self.classes):
                if class_name.startswith("theme-"):
                    self.remove_class(class_name)
            self.add_class(f"theme-{theme_name}")
        self._apply_runtime_theme_tokens()
        try:
            self.query_one("#login_url", Input).focus()
        except Exception:  # noqa: BLE001
            self.query_one("#login_username", Input).focus()

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
        self.query_one("#login_modal_dialog", Vertical).set_styles(
            f"background: {surface}; border: tall {border};"
        )
        self.query_one("#login_modal_actions", Horizontal).set_styles(
            "background: transparent; background-tint: transparent;"
        )
        self.query_one("#login_submit", Button).set_styles(
            f"background: {panel}; color: {primary}; border: round {primary}; "
            "tint: transparent; background-tint: transparent;"
        )
        self.query_one("#login_cancel", Button).set_styles(
            f"background: transparent; color: {muted}; "
            f"border: round {border}; tint: transparent; background-tint: transparent;"
        )

    def _show_error(self, msg: str) -> None:
        self.query_one("#login_error", Static).update(msg)

    def action_cancel_login(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#login_cancel")
    def cancel_pressed(self) -> None:
        self.dismiss(False)

    @on(Button.Pressed, "#login_submit")
    async def submit_pressed(self) -> None:
        try:
            url_input = self.query_one("#login_url", Input)
            url = url_input.value.strip()
            if not url:
                self._show_error("NetBox URL is required.")
                url_input.focus()
                return
            self.app.client.config.base_url = url
        except Exception:  # noqa: BLE001
            pass  # URL field absent — base_url already configured

        username = self.query_one("#login_username", Input).value.strip()
        password = self.query_one("#login_password", Input).value

        if not username:
            self._show_error("Username is required.")
            self.query_one("#login_username", Input).focus()
            return
        if not password:
            self._show_error("Password is required.")
            self.query_one("#login_password", Input).focus()
            return

        self._show_error("")
        try:
            response = await self.app.client.create_token(username, password)
        except Exception as exc:  # noqa: BLE001
            self._show_error(f"Connection error: {exc}")
            return

        if 200 <= response.status < 300:
            self.dismiss(True)
        else:
            self._show_error("Invalid username or password.")
            self.query_one("#login_password", Input).focus()
