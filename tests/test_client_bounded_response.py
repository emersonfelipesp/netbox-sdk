"""Transport bounds used by the semantic plugin bridge."""

from __future__ import annotations

from typing import Any

import pytest

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.exceptions import ResponseSizeLimitError

pytestmark = pytest.mark.suite_sdk


class _BoundedContent:
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    async def iter_chunked(self, size: int):
        del size
        for chunk in self.chunks:
            yield chunk


class _BoundedResponse:
    def __init__(
        self,
        *,
        status: int = 200,
        chunks: list[bytes] | None = None,
        headers: dict[str, str] | None = None,
        charset: str = "utf-8",
    ) -> None:
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}
        self.content = _BoundedContent(chunks or [b'{"ok":true}'])
        self.charset = charset

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _BoundedSession:
    def __init__(self, response: _BoundedResponse) -> None:
        self.response = response
        self.request_kwargs: dict[str, Any] = {}

    def request(self, **kwargs: Any) -> _BoundedResponse:
        self.request_kwargs = kwargs
        return self.response


async def test_bounded_request_disables_redirects_and_bypasses_cache(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    session = _BoundedSession(_BoundedResponse(status=307))
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))

    async def get_session():
        return session

    monkeypatch.setattr(client, "_get_session", get_session)

    def cache_must_not_run(**kwargs: Any):
        del kwargs
        raise AssertionError("bounded requests must bypass the HTTP cache")

    monkeypatch.setattr(client, "_cache_policy", cache_must_not_run)

    response = await client.request_bounded(
        "GET", "/api/plugins/proxbox/mcp/", max_response_bytes=1024
    )

    assert response.status == 307
    assert session.request_kwargs["allow_redirects"] is False


async def test_bounded_request_rejects_content_length_before_streaming(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(headers={"Content-Length": "4097"})
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))

    with pytest.raises(ResponseSizeLimitError, match="4096"):
        await client.request_bounded("GET", "/api/plugins/proxbox/mcp/", max_response_bytes=4096)


async def test_bounded_request_counts_streamed_decompressed_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(
        chunks=[b"x" * 3000, b"y" * 2000],
        headers={"Content-Encoding": "gzip"},
    )
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))

    with pytest.raises(ResponseSizeLimitError, match="4096"):
        await client.request_bounded("GET", "/api/plugins/proxbox/mcp/", max_response_bytes=4096)


async def test_bounded_head_ignores_representation_content_length(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(
        chunks=[b""],
        headers={"Content-Length": "4097"},
    )
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))

    result = await client.request_bounded(
        "HEAD", "/api/plugins/proxbox/status/", max_response_bytes=4096
    )

    assert result.status == 200
    assert result.text == ""


async def test_bounded_request_preserves_predecode_streamed_byte_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    encoded = (b"\x1b(B" * 100) + b"{}"
    response = _BoundedResponse(
        chunks=[encoded],
        headers={"Content-Type": "application/json; charset=iso-2022-jp"},
        charset="iso-2022-jp",
    )
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com"))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))

    result = await client.request_bounded(
        "GET", "/api/plugins/proxbox/mcp/", max_response_bytes=1024
    )

    assert result.text == "{}"
    assert result.body_size_bytes == len(encoded)


async def _async_value(value: object):
    return value


def _no_cache(client: NetBoxApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "_cache_policy", lambda **kwargs: None)


async def test_ordinary_request_is_bounded_by_the_configured_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    """A plain ``request()`` never reads an unbounded body."""

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(chunks=[b"x" * 3000, b"y" * 2000])
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", max_response_bytes=4096))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    _no_cache(client, monkeypatch)

    with pytest.raises(ResponseSizeLimitError, match="4096"):
        await client.request("GET", "/api/dcim/devices/")


async def test_ordinary_request_rejects_declared_length_over_the_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(headers={"Content-Length": "4097"})
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", max_response_bytes=4096))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    _no_cache(client, monkeypatch)

    with pytest.raises(ResponseSizeLimitError, match="4096"):
        await client.request("GET", "/api/dcim/devices/")


async def test_ordinary_request_within_the_default_bound_reports_its_size(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(chunks=[b'{"ok":', b"true}"])
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", max_response_bytes=4096))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    _no_cache(client, monkeypatch)

    result = await client.request("GET", "/api/dcim/devices/")

    assert result.text == '{"ok":true}'
    assert result.body_size_bytes == 11


async def test_explicit_bound_overrides_the_configured_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    response = _BoundedResponse(chunks=[b"x" * 100])
    session = _BoundedSession(response)
    client = NetBoxApiClient(Config(base_url="https://netbox.example.com", max_response_bytes=4096))
    monkeypatch.setattr(client, "_get_session", lambda: _async_value(session))
    _no_cache(client, monkeypatch)

    with pytest.raises(ResponseSizeLimitError, match="64"):
        await client._request_impl("GET", "/api/dcim/devices/", max_response_bytes=64)


def test_config_default_bounds_are_positive_and_overridable() -> None:
    from netbox_sdk.config import DEFAULT_MAX_RESPONSE_BYTES, DEFAULT_MAX_SSE_BLOCK_BYTES

    cfg = Config(base_url="https://netbox.example.com")
    assert cfg.max_response_bytes == DEFAULT_MAX_RESPONSE_BYTES == 64 * 1024 * 1024
    assert cfg.max_sse_block_bytes == DEFAULT_MAX_SSE_BLOCK_BYTES == 1024 * 1024
    assert (
        Config(base_url="https://netbox.example.com", max_response_bytes="2048").max_response_bytes
        == 2048
    )


@pytest.mark.parametrize("value", [0, -1, "0", "abc", None, "", True, "inf", "nan"])
def test_config_rejects_bounds_that_would_unbound_the_read(value: object) -> None:
    from netbox_sdk.config import DEFAULT_MAX_RESPONSE_BYTES, DEFAULT_MAX_SSE_BLOCK_BYTES

    cfg = Config(
        base_url="https://netbox.example.com",
        max_response_bytes=value,
        max_sse_block_bytes=value,
    )
    assert cfg.max_response_bytes == DEFAULT_MAX_RESPONSE_BYTES
    assert cfg.max_sse_block_bytes == DEFAULT_MAX_SSE_BLOCK_BYTES


def test_max_response_bytes_env_applies_to_the_default_profile(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from netbox_sdk.config import MAX_RESPONSE_BYTES_ENV_VAR, load_config

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv(MAX_RESPONSE_BYTES_ENV_VAR, "8192")

    assert load_config().max_response_bytes == 8192


@pytest.mark.parametrize("value", [0, -3, "0", "-1", "nan", "inf", float("inf"), float("nan")])
def test_config_rejects_timeouts_that_disable_the_deadline(value: object) -> None:
    from netbox_sdk.config import DEFAULT_TIMEOUT

    assert Config(base_url="https://netbox.example.com", timeout=value).timeout == DEFAULT_TIMEOUT


def test_config_keeps_a_valid_timeout() -> None:
    assert Config(base_url="https://netbox.example.com", timeout="2.5").timeout == 2.5
