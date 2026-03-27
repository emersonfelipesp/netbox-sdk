"""Tests for demo authentication flows, page parsing, and token extraction."""

from __future__ import annotations

import pytest

from netbox_sdk.demo_auth import (
    DEMO_CREATE_USER_URL,
    LOGIN_URL,
    DemoToken,
    _create_demo_user,
    _extract_page_error,
    _is_existing_demo_user_error,
    _login,
    _parse_token,
    _parse_v1_token,
)

pytestmark = pytest.mark.suite_sdk


class _Locator:
    def __init__(self, page: _FakePage, kind: str, value: str):
        self.page = page
        self.kind = kind
        self.value = value

    def fill(self, text: str) -> None:
        self.page.calls.append(("fill", self.kind, self.value, text))

    def click(self) -> None:
        self.page.calls.append(("click", self.kind, self.value))
        if self.kind == "role" and self.value == "Create & Sign In":
            self.page.url = f"{self.page.base_url}/"
        elif self.kind == "role" and self.value == "Sign In":
            self.page.url = f"{self.page.base_url}/"


class _FakePage:
    def __init__(self, *, url: str = "", base_url: str = "https://demo.netbox.dev"):
        self.url = url
        self.base_url = base_url
        self.calls: list[tuple[object, ...]] = []
        self.body_text = ""

    def goto(self, url: str, wait_until: str | None = None) -> None:
        self.calls.append(("goto", url, wait_until))
        self.url = url

    def get_by_label(self, name: str) -> _Locator:
        return _Locator(self, "label", name)

    def get_by_role(self, role: str, name: str) -> _Locator:
        assert role == "button"
        return _Locator(self, "role", name)

    def wait_for_load_state(self, state: str) -> None:
        self.calls.append(("wait_for_load_state", state))

    def wait_for_url(self, pattern: str) -> None:
        self.calls.append(("wait_for_url", pattern))

    class _BodyLocator:
        def __init__(self, page: _FakePage):
            self.page = page

        def inner_text(self) -> str:
            return self.page.body_text

    def locator(self, selector: str):
        if selector == "body":
            return self._BodyLocator(self)
        raise AssertionError(f"Unexpected selector: {selector}")


def test_create_demo_user_hits_plugin_page_first() -> None:
    page = _FakePage()

    created = _create_demo_user(page, username="demo-user", password="demo-pass")

    assert created is True
    assert page.calls[0] == ("goto", DEMO_CREATE_USER_URL, "domcontentloaded")
    assert ("fill", "label", "Username", "demo-user") in page.calls
    assert ("fill", "label", "Password", "demo-pass") in page.calls
    assert ("click", "role", "Create & Sign In") in page.calls


def test_create_demo_user_returns_false_for_existing_username_error() -> None:
    page = _FakePage()
    page.body_text = (
        "Server Error\n"
        'duplicate key value violates unique constraint "users_user_username_key"\n'
        "DETAIL:  Key (username)=(demo-user) already exists.\n"
    )

    created = _create_demo_user(page, username="demo-user", password="demo-pass")

    assert created is False
    assert ("wait_for_load_state", "networkidle") not in page.calls


def test_login_visits_standard_login_after_user_creation() -> None:
    page_base = "https://demo.netbox.dev"
    page = _FakePage(url=f"{page_base}/")

    _login(page, username="demo-user", password="demo-pass")

    assert page.calls[0] == ("goto", LOGIN_URL, "domcontentloaded")
    assert ("fill", "label", "Username", "demo-user") in page.calls
    assert ("fill", "label", "Password", "demo-pass") in page.calls
    assert ("click", "role", "Sign In") in page.calls
    assert page.url == f"{page_base}/"


def test_parse_token_splits_netbox_v2_token() -> None:
    token = _parse_token("nbt_abc.def")

    assert token == DemoToken(version="v2", key="abc", secret="def")


def test_parse_v1_token_keeps_plain_token() -> None:
    token = _parse_v1_token("A" * 40)

    assert token == DemoToken(version="v1", key=None, secret="A" * 40)


def test_login_skips_form_when_already_redirected() -> None:
    page = _FakePage()

    def _redirecting_goto(url: str, wait_until: str | None = None) -> None:
        page.calls.append(("goto", url, wait_until))
        page.url = f"{page.base_url}/"

    page.goto = _redirecting_goto  # type: ignore[method-assign]

    _login(page, username="demo-user", password="demo-pass")

    assert page.calls == [("goto", LOGIN_URL, "domcontentloaded")]


def test_extract_page_error_returns_following_line() -> None:
    class _ErrorPage:
        class _BodyLocator:
            def inner_text(self) -> str:
                return "Something\nError\nUnable to save v2 tokens: API_TOKEN_PEPPERS is not defined.\n"

        def locator(self, selector: str):
            assert selector == "body"
            return self._BodyLocator()

    assert (
        _extract_page_error(_ErrorPage())
        == "Unable to save v2 tokens: API_TOKEN_PEPPERS is not defined."
    )


def test_existing_demo_user_error_detection_matches_username() -> None:
    page = _FakePage()
    page.body_text = (
        "duplicate key value violates unique constraint\n"
        "DETAIL:  Key (username)=(demo-user) already exists.\n"
    )

    assert _is_existing_demo_user_error(page, username="demo-user") is True
    assert _is_existing_demo_user_error(page, username="other-user") is False
