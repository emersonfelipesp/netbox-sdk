"""Demo-environment authentication helpers for provisioning and parsing NetBox demo tokens."""

from __future__ import annotations

from pydantic import BaseModel

from .config import DEMO_BASE_URL, Config, normalize_base_url

DEMO_CREATE_USER_URL = f"{DEMO_BASE_URL}/plugins/demo/login/"
LOGIN_URL = f"{DEMO_BASE_URL}/login/"
TOKENS_URL = f"{DEMO_BASE_URL}/user/api-tokens/"


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


def provision_demo_token(
    *,
    username: str,
    password: str,
    headless: bool = False,
    token_name: str = "nbx-demo",
) -> DemoToken:
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
                    print(f"Demo user '{username}' already exists. Proceeding to login.")
                _login(page, username=username, password=password)
                token_value = _create_token(page, token_name=token_name)
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise RuntimeError(
            "Timed out while automating demo.netbox.dev. "
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
        raise RuntimeError(f"Failed to automate demo.netbox.dev login: {detail}") from exc
    return _parse_v1_token(token_value)


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


def _create_token(page: object, *, token_name: str) -> str:
    page.goto(TOKENS_URL, wait_until="domcontentloaded")

    add_link = page.get_by_role("link", name="Add a Token")
    add_button = page.get_by_role("button", name="Add a Token")
    if add_link.count():
        add_link.first.click()
    else:
        add_button.first.click()

    version_field = page.locator("#id_version")
    if version_field.count():
        version_field.select_option("1")

    token_input = page.locator("#id_token")
    token_input.wait_for()
    token_value = token_input.input_value().strip()
    if not token_value:
        raise RuntimeError("Demo token form did not provide a v1 token value.")

    description_field = page.locator("#id_description")
    if description_field.count():
        description_field.fill(token_name)

    create_button = page.get_by_role("button", name="Create")
    create_button.first.click()

    try:
        page.wait_for_url(f"{TOKENS_URL}**", timeout=10000)
    except Exception as exc:  # noqa: BLE001
        error_text = _extract_page_error(page)
        if error_text:
            raise RuntimeError(f"NetBox demo rejected token creation: {error_text}") from exc
        raise RuntimeError("Timed out waiting for NetBox demo to finish token creation.") from exc

    return token_value


def _extract_token_from_text(text: str) -> str:
    for part in text.split():
        if part.startswith("nbt_") and "." in part:
            return part.strip()
    return ""


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
