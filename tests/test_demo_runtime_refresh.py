"""Tests for automatic demo profile repair during runtime config loading."""

from __future__ import annotations

import asyncio

import pytest

from netbox_cli.runtime import _RUNTIME_CONFIGS, _ensure_demo_runtime_config
from netbox_sdk.client import ApiResponse
from netbox_sdk.config import DEMO_BASE_URL, Config

pytestmark = pytest.mark.suite_cli


def test_ensure_demo_runtime_config_repairs_invalid_v1_token(monkeypatch) -> None:
    _RUNTIME_CONFIGS.clear()
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="expired-v1-token",
        demo_username="demo-user",
        demo_password="demo-pass",
        timeout=30.0,
    )
    refreshed = Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="fresh-v1-token",
        demo_username="demo-user",
        demo_password="demo-pass",
        timeout=30.0,
    )

    class _FakeClient:
        async def request(self, method: str, path: str) -> ApiResponse:
            assert (method, path) == ("GET", "/api/status/")
            return ApiResponse(status=403, text='{"detail": "Invalid v1 token"}', headers={})

    monkeypatch.setattr("netbox_cli.runtime.load_profile_config", lambda profile: cfg)
    monkeypatch.setattr(
        "netbox_cli.runtime.run_with_spinner", lambda awaitable: asyncio.run(awaitable)
    )
    monkeypatch.setattr(
        "netbox_cli.runtime._get_client_for_config", lambda current: _FakeClient()
    )
    monkeypatch.setattr(
        "netbox_sdk.demo_auth.refresh_demo_profile",
        lambda existing, headless=True: refreshed,
        raising=False,
    )

    saved: dict[str, object] = {}
    monkeypatch.setattr(
        "netbox_cli.runtime.save_profile_config",
        lambda profile, current: saved.update({"profile": profile, "cfg": current}),
    )

    result = _ensure_demo_runtime_config()

    assert result.token_secret == "fresh-v1-token"
    assert saved["profile"] == "demo"
    assert saved["cfg"].token_secret == "fresh-v1-token"


def test_ensure_demo_runtime_config_skips_repair_without_saved_credentials(monkeypatch) -> None:
    _RUNTIME_CONFIGS.clear()
    cfg = Config(
        base_url=DEMO_BASE_URL,
        token_version="v1",
        token_secret="expired-v1-token",
        timeout=30.0,
    )

    monkeypatch.setattr("netbox_cli.runtime.load_profile_config", lambda profile: cfg)

    result = _ensure_demo_runtime_config()

    assert result.token_secret == "expired-v1-token"
