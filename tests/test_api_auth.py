from __future__ import annotations

from collections import deque

import pytest

from netbox_cli.api import ApiResponse, NetBoxApiClient
from netbox_cli.config import (
    Config,
    authorization_header_value,
    is_runtime_config_complete,
)


def test_authorization_header_value_v2() -> None:
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v2",
        token_key="abc",
        token_secret="def",
    )

    assert authorization_header_value(cfg) == "Bearer nbt_abc.def"


def test_authorization_header_value_v1() -> None:
    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )

    assert authorization_header_value(cfg) == "Token plain-token"


def test_runtime_config_complete_v1_without_token_key() -> None:
    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v1",
        token_secret="plain-token",
    )

    assert is_runtime_config_complete(cfg) is True


def test_api_client_rejects_absolute_request_urls(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com",
            token_version="v1",
            token_secret="plain-token",
        )
    )

    with pytest.raises(
        ValueError, match="relative to the configured NetBox base URL"
    ):
        client.build_url("https://evil.example.com/api/status/")


def test_api_client_rejects_request_paths_with_query_or_fragment(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    client = NetBoxApiClient(
        Config(
            base_url="https://netbox.example.com",
            token_version="v1",
            token_secret="plain-token",
        )
    )

    with pytest.raises(ValueError, match="must not include query parameters"):
        client.build_url("/api/status/?format=json")

    with pytest.raises(ValueError, match="must not include query parameters"):
        client.build_url("/api/status/#frag")


@pytest.mark.asyncio
async def test_api_client_retries_with_v1_on_invalid_v2(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v2",
        token_key="legacy",
        token_secret="plain-v1-token",
    )
    client = NetBoxApiClient(cfg)

    calls: list[str] = []
    responses = deque(
        [
            ApiResponse(status=403, text="Invalid v2 token", headers={}),
            ApiResponse(status=200, text='{"ok": true}', headers={}),
        ]
    )

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs["authorization"] or "")
        return responses.popleft()

    class _FakeClientSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeClientTimeout:
        def __init__(self, total):
            self.total = total

    class _FakeAiohttp:
        ClientSession = _FakeClientSession
        ClientTimeout = _FakeClientTimeout

    import sys

    monkeypatch.setitem(sys.modules, "aiohttp", _FakeAiohttp())
    monkeypatch.setattr(
        NetBoxApiClient, "_request_once", _fake_request_once, raising=True
    )

    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 200
    assert calls[0] == "Bearer nbt_legacy.plain-v1-token"
    assert calls[1] == "Token plain-v1-token"


@pytest.mark.asyncio
async def test_api_client_does_not_retry_non_auth_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = Config(
        base_url="https://demo.netbox.dev",
        token_version="v2",
        token_key="legacy",
        token_secret="plain-v1-token",
    )
    client = NetBoxApiClient(cfg)

    calls: list[str] = []

    async def _fake_request_once(self, session, **kwargs):
        calls.append(kwargs["authorization"] or "")
        return ApiResponse(status=500, text="server error", headers={})

    class _FakeClientSession:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _FakeClientTimeout:
        def __init__(self, total):
            self.total = total

    class _FakeAiohttp:
        ClientSession = _FakeClientSession
        ClientTimeout = _FakeClientTimeout

    import sys

    monkeypatch.setitem(sys.modules, "aiohttp", _FakeAiohttp())
    monkeypatch.setattr(
        NetBoxApiClient, "_request_once", _fake_request_once, raising=True
    )

    response = await client.request("GET", "/api/dcim/devices/")

    assert response.status == 500
    assert calls == ["Bearer nbt_legacy.plain-v1-token"]
