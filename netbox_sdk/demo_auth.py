"""Demo-environment authentication helpers for provisioning and parsing NetBox demo tokens."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from pydantic import BaseModel

from netbox_sdk.config import DEMO_BASE_URL, Config, normalize_base_url

DEMO_CREATE_USER_URL = f"{DEMO_BASE_URL}/plugins/demo/login/"
LOGIN_URL = f"{DEMO_BASE_URL}/login/"
TOKENS_URL = f"{DEMO_BASE_URL}/user/api-tokens/"
TOKENS_PROVISION_URL = f"{DEMO_BASE_URL}/api/users/tokens/provision/"


class DemoToken(BaseModel):
    version: str
    key: str | None
    secret: str


def bootstrap_demo_profile(
    *,
    username: str,
    password: str,
    timeout: float,
    headless: bool = False,
    token_name: str = "nbx-demo",
) -> Config:
    token = provision_demo_token(
        username=username,
        password=password,
        headless=headless,
        token_name=token_name,
    )
    return Config(
        base_url=normalize_base_url(DEMO_BASE_URL),
        token_version=token.version,
        token_key=token.key,
        token_secret=token.secret,
        timeout=timeout,
    )


def refresh_demo_profile(existing: Config, *, headless: bool = True) -> Config:
    """Re-run demo bootstrap using already saved demo credentials."""
    if not existing.demo_username or not existing.demo_password:
        raise RuntimeError("Saved demo credentials are not available for token refresh.")
    refreshed = bootstrap_demo_profile(
        username=existing.demo_username,
        password=existing.demo_password,
        timeout=existing.timeout,
        headless=headless,
    )
    refreshed.demo_username = existing.demo_username
    refreshed.demo_password = existing.demo_password
    return refreshed


def provision_demo_token(
    *,
    username: str,
    password: str,
    headless: bool = False,
    token_name: str = "nbx-demo",
) -> DemoToken:
    # Try the REST API path first — it works without Playwright if the account exists.
    # If the account does not exist yet (401/403), use Playwright to register it.
    try:
        return _provision_token_via_api(username=username, password=password)
    except _TokenProvisionError:
        pass  # account likely doesn't exist — fall through to Playwright registration

    _register_demo_user_via_playwright(username=username, password=password, headless=headless)

    try:
        return _provision_token_via_api(username=username, password=password)
    except _TokenProvisionError as exc:
        raise RuntimeError(
            f"Token provisioning failed for '{username}' after account registration: {exc}"
        ) from exc


def _provision_token_via_api(*, username: str, password: str) -> DemoToken:
    """POST to /api/users/tokens/provision/ and return a v2 DemoToken.

    Raises _TokenProvisionError when the HTTP response indicates the credentials
    are not valid (401/403) so the caller can fall back to account registration.
    Raises RuntimeError for unexpected errors.
    """
    payload = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        TOKENS_PROVISION_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise _TokenProvisionError(f"HTTP {exc.code}: credentials not accepted") from exc
        raw = exc.read().decode(errors="replace")
        raise RuntimeError(f"Token provisioning returned HTTP {exc.code}: {raw[:200]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Token provisioning network error: {exc.reason}") from exc

    # Validate the expected fields
    token_key = body.get("key", "")
    token_secret = body.get("token", "")
    if not token_key or not token_secret:
        raise RuntimeError(f"Unexpected token provisioning response shape — got keys: {list(body)}")
    return DemoToken(version="v2", key=token_key, secret=token_secret)


class _TokenProvisionError(Exception):
    """Raised when the provision endpoint rejects the credentials (account absent)."""


def _register_demo_user_via_playwright(*, username: str, password: str, headless: bool) -> None:
    """Use Playwright to register a new demo account via the plugin UI."""
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Playwright is required for `nbx demo init`. Install it with:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        ) from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            page = browser.new_page()
            try:
                user_created = _create_demo_user(page, username=username, password=password)
                if not user_created:
                    print(f"Demo user '{username}' already exists.")
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Timed out while registering demo account on demo.netbox.dev. "
            "Verify credentials and ensure Playwright browsers are installed with "
            "`playwright install chromium`."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        detail = str(exc)
        if (
            "Missing X server or $DISPLAY" in detail
            or "headed browser without having a XServer running" in detail
        ):
            raise RuntimeError(
                "Playwright was started in headed mode, but no X server is available.\n"
                "Use headless mode, or run the command under xvfb.\n"
                "Examples:\n"
                "  nbx demo\n"
                "  xvfb-run nbx demo --headed"
            ) from exc
        if "error while loading shared libraries" in detail or "BrowserType.launch" in detail:
            raise RuntimeError(
                "Playwright Chromium could not start because system libraries are missing.\n"
                "Install browser dependencies with:\n"
                "  playwright install --with-deps chromium\n"
                "If that is unavailable on your system, install the missing shared libraries and retry."
            ) from exc
        raise RuntimeError(f"Failed to register demo account on demo.netbox.dev: {detail}") from exc


def _create_demo_user(page: object, *, username: str, password: str) -> bool:
    page.goto(DEMO_CREATE_USER_URL, wait_until="domcontentloaded")
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Create & Sign In").click()
    page.wait_for_load_state("domcontentloaded")

    if _is_existing_demo_user_error(page, username=username):
        return False

    page.wait_for_load_state("networkidle")
    return True


def _login(page: object, *, username: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    if "/login/" not in page.url:
        return
    page.get_by_label("Username").fill(username)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(f"{DEMO_BASE_URL}/**")
    if "/login/" in page.url:
        raise RuntimeError("Demo login failed. Check the provided username and password.")


def _extract_page_error(page: object) -> str:
    body_text = page.locator("body").inner_text()
    if "Error" in body_text:
        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        for index, line in enumerate(lines):
            if line == "Error" and index + 1 < len(lines):
                return lines[index + 1]
    return ""


def _is_existing_demo_user_error(page: object, *, username: str) -> bool:
    body_text = page.locator("body").inner_text()
    lowered = body_text.lower()
    return (
        "duplicate key value violates unique constraint" in lowered
        and f"(username)=({username.lower()}) already exists" in lowered
    )


def _parse_token(token_value: str) -> DemoToken:
    stripped = token_value.strip()
    if not stripped.startswith("nbt_") or "." not in stripped:
        raise RuntimeError("Unexpected token format returned by demo.netbox.dev.")
    key, secret = stripped.split(".", 1)
    return DemoToken(version="v2", key=key.removeprefix("nbt_"), secret=secret)


def _parse_v1_token(token_value: str) -> DemoToken:
    stripped = token_value.strip()
    if len(stripped) < 40:
        raise RuntimeError("Unexpected v1 token format returned by demo.netbox.dev.")
    return DemoToken(version="v1", key=None, secret=stripped)
