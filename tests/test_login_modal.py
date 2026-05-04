"""Tests for the TUI login modal (issue #12)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Input, Static

from netbox_sdk.client import ApiResponse
from netbox_tui.login_modal import LoginModal

pytestmark = pytest.mark.suite_tui


# ---------------------------------------------------------------------------
# Minimal host app for modal testing
# ---------------------------------------------------------------------------


class _LoginHost(App[bool | None]):
    """Minimal app that immediately pushes LoginModal and captures the result.

    push_screen_wait must be called from a @work context (Textual requirement).
    """

    def __init__(self, client: object) -> None:
        super().__init__()
        self.client = client
        self.login_result: bool | None = None

    def compose(self) -> ComposeResult:
        return iter([])

    def on_mount(self) -> None:
        self._show_login()

    @work(thread=False)
    async def _show_login(self) -> None:
        self.login_result = await self.push_screen_wait(LoginModal())
        self.exit()


def _make_client(*, base_url: str | None = "https://netbox.example.com") -> MagicMock:
    client = MagicMock()
    client.config.base_url = base_url
    client.config.token_version = "v2"
    client.config.token_key = None
    client.config.token_secret = None
    return client


def _ok_response(token: str = "abc123xyz") -> ApiResponse:
    return ApiResponse(status=200, text=f'{{"key": "{token}"}}', headers={})


def _error_response(status: int = 401) -> ApiResponse:
    return ApiResponse(status=status, text='{"detail": "invalid"}', headers={})


async def _wait_for_modal(pilot, attempts: int = 5) -> None:
    """Pause until the LoginModal is the active screen (up to `attempts` cycles)."""
    for _ in range(attempts):
        await pilot.pause()
        if isinstance(pilot.app.screen, LoginModal):
            return
    raise TimeoutError("LoginModal did not appear after waiting")


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------


async def test_successful_login_dismisses_true() -> None:
    client = _make_client()

    async def _create_token(username: str, password: str) -> ApiResponse:
        del username, password
        client.config.token_version = "v1"
        client.config.token_secret = "abc123xyz"
        return _ok_response()

    client.create_token = AsyncMock(side_effect=_create_token)

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        modal.query_one("#login_username", Input).value = "admin"
        modal.query_one("#login_password", Input).value = "password123"
        await pilot.click("#login_submit")
        await pilot.pause()
        await pilot.pause()

    assert app.login_result is True
    client.create_token.assert_called_once_with("admin", "password123")
    assert client.config.token_version == "v1"
    assert client.config.token_secret == "abc123xyz"


# ---------------------------------------------------------------------------
# Failure path
# ---------------------------------------------------------------------------


async def test_failed_login_shows_error_and_stays_open() -> None:
    client = _make_client()
    client.create_token = AsyncMock(return_value=_error_response(401))

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        modal.query_one("#login_username", Input).value = "admin"
        modal.query_one("#login_password", Input).value = "wrongpassword"
        await pilot.click("#login_submit")
        await pilot.pause()
        await pilot.pause()

        # Modal should still be the active screen
        assert isinstance(app.screen, LoginModal)
        error_text = str(modal.query_one("#login_error", Static).content)
        assert error_text.strip()  # non-empty error message

    assert app.login_result is None


# ---------------------------------------------------------------------------
# Cancel path
# ---------------------------------------------------------------------------


async def test_cancel_button_dismisses_false() -> None:
    client = _make_client()
    client.create_token = AsyncMock()

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)
        await pilot.click("#login_cancel")
        await pilot.pause()
        await pilot.pause()

    assert app.login_result is False
    client.create_token.assert_not_called()


async def test_escape_key_dismisses_false() -> None:
    client = _make_client()
    client.create_token = AsyncMock()

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)
        await pilot.press("escape")
        await pilot.pause()
        await pilot.pause()

    assert app.login_result is False
    client.create_token.assert_not_called()


# ---------------------------------------------------------------------------
# URL field visibility
# ---------------------------------------------------------------------------


async def test_url_field_shown_when_base_url_missing() -> None:
    client = _make_client(base_url=None)
    client.create_token = AsyncMock()

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        input_ids = [w.id for w in modal.query(Input)]
        assert "login_url" in input_ids, f"expected login_url input, got {input_ids}"
        await pilot.click("#login_cancel")
        await pilot.pause()


async def test_url_field_hidden_when_base_url_set() -> None:
    client = _make_client(base_url="https://netbox.example.com")
    client.create_token = AsyncMock()

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        input_ids = [w.id for w in modal.query(Input)]
        assert "login_url" not in input_ids, f"login_url should be absent, got {input_ids}"
        await pilot.click("#login_cancel")
        await pilot.pause()


# ---------------------------------------------------------------------------
# Connection error path
# ---------------------------------------------------------------------------


async def test_connection_error_shows_error_message() -> None:
    client = _make_client()
    client.create_token = AsyncMock(side_effect=ConnectionError("connection refused"))

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        modal.query_one("#login_username", Input).value = "admin"
        modal.query_one("#login_password", Input).value = "pass"
        await pilot.click("#login_submit")
        await pilot.pause()
        await pilot.pause()

        assert isinstance(app.screen, LoginModal)
        error_text = str(modal.query_one("#login_error", Static).content)
        assert "connection" in error_text.lower() or "error" in error_text.lower()

    assert app.login_result is None


async def test_url_input_is_normalized_before_login() -> None:
    client = _make_client(base_url=None)

    async def _create_token(username: str, password: str) -> ApiResponse:
        del username, password
        client.config.token_version = "v1"
        client.config.token_secret = "abc123xyz"
        return _ok_response()

    client.create_token = AsyncMock(side_effect=_create_token)

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        modal.query_one("#login_url", Input).value = "netbox.example.com/api/"
        modal.query_one("#login_username", Input).value = "admin"
        modal.query_one("#login_password", Input).value = "password123"
        await pilot.click("#login_submit")
        await pilot.pause()
        await pilot.pause()

    assert app.login_result is True
    assert client.config.base_url == "https://netbox.example.com/api"


async def test_success_without_token_stays_open() -> None:
    client = _make_client()
    client.create_token = AsyncMock(return_value=_ok_response())

    app = _LoginHost(client)
    async with app.run_test(size=(100, 30)) as pilot:
        await _wait_for_modal(pilot)

        modal = app.screen
        modal.query_one("#login_username", Input).value = "admin"
        modal.query_one("#login_password", Input).value = "password123"
        await pilot.click("#login_submit")
        await pilot.pause()
        await pilot.pause()

        assert isinstance(app.screen, LoginModal)
        error_text = str(modal.query_one("#login_error", Static).content)
        assert "no API token" in error_text

    assert app.login_result is None
