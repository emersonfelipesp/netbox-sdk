"""Tests for TLS verification helpers and config wiring."""

from __future__ import annotations

import ssl

import pytest

from netbox_sdk.config import SSL_VERIFY_ENV_VAR, Config, load_profile_config, save_config
from netbox_sdk.http_ssl import (
    connector_for_config,
    is_certificate_verify_failure,
    is_certificate_verify_failure_text,
)

pytestmark = pytest.mark.suite_sdk


def test_is_certificate_verify_failure_direct() -> None:
    exc = ssl.SSLCertVerificationError(1, "certificate verify failed")
    assert is_certificate_verify_failure(exc) is True


def test_is_certificate_verify_failure_wrapped() -> None:
    inner = ssl.SSLCertVerificationError(1, "certificate verify failed")
    try:
        raise RuntimeError("wrap") from inner
    except RuntimeError as outer:
        assert is_certificate_verify_failure(outer) is True


def test_is_certificate_verify_failure_text() -> None:
    assert is_certificate_verify_failure_text("certificate verify failed: self-signed") is True
    assert is_certificate_verify_failure_text(None) is False
    assert is_certificate_verify_failure_text("connection refused") is False


@pytest.mark.asyncio
async def test_connector_https_verify_off() -> None:
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="t",
        ssl_verify=False,
    )
    conn = connector_for_config(cfg)
    assert conn is not None
    await conn.close()


def test_connector_http_no_custom_connector() -> None:
    cfg = Config(
        base_url="http://netbox.example.com",
        token_version="v1",
        token_secret="t",
        ssl_verify=False,
    )
    assert connector_for_config(cfg) is None


def test_is_certificate_verify_failure_aiohttp_connector_certificate() -> None:
    import aiohttp

    inner = ssl.SSLCertVerificationError(1, "certificate verify failed")
    exc = aiohttp.ClientConnectorCertificateError(None, inner)
    assert is_certificate_verify_failure(exc) is True


def test_connector_https_verify_true_or_none_uses_default() -> None:
    for ssl_verify in (None, True):
        cfg = Config(
            base_url="https://netbox.example.com",
            token_version="v1",
            token_secret="t",
            ssl_verify=ssl_verify,
        )
        assert connector_for_config(cfg) is None


def test_config_ssl_verify_roundtrip_save_load(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = Config(
        base_url="https://a.example.com",
        token_key="k",
        token_secret="s",
        ssl_verify=False,
    )
    save_config(cfg)
    loaded = load_profile_config("default")
    assert loaded.ssl_verify is False


def test_load_profile_respects_ssl_verify_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    save_config(
        Config(
            base_url="https://a.example.com",
            token_key="k",
            token_secret="s",
            ssl_verify=None,
        )
    )
    monkeypatch.setenv(SSL_VERIFY_ENV_VAR, "0")
    cfg = load_profile_config("default")
    assert cfg.ssl_verify is False
    monkeypatch.setenv(SSL_VERIFY_ENV_VAR, "1")
    cfg = load_profile_config("default")
    assert cfg.ssl_verify is True
