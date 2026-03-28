"""Security tests for the netbox_sdk package.

Covers: SSRF via request path manipulation, base URL injection, path traversal,
cache key isolation, HTTP header injection through token values, and credential
field handling.
"""

from __future__ import annotations

import pytest

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config, authorization_header_value, normalize_base_url
from netbox_sdk.http_cache import build_cache_key

pytestmark = pytest.mark.suite_sdk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _client(tmp_path, monkeypatch, *, base_url: str = "https://netbox.example.com") -> NetBoxApiClient:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return NetBoxApiClient(
        Config(base_url=base_url, token_version="v1", token_secret="testtoken")
    )


# ---------------------------------------------------------------------------
# SSRF — scheme/netloc in request path
# ---------------------------------------------------------------------------

def test_ssrf_absolute_http_url_in_request_path_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject an absolute HTTP URL supplied as a request path."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="relative to the configured NetBox base URL"):
        client.build_url("http://evil.example.com/api/status/")


def test_ssrf_absolute_https_url_in_request_path_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject an absolute HTTPS URL supplied as a request path."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="relative to the configured NetBox base URL"):
        client.build_url("https://evil.example.com/api/dcim/devices/")


def test_ssrf_network_path_reference_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject network-path references like //evil.example/."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="relative to the configured NetBox base URL"):
        client.build_url("//evil.example.com/api/status/")


def test_ssrf_path_with_query_string_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject a path that embeds a query string."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="must not include query parameters"):
        client.build_url("/api/dcim/devices/?q=evil")


def test_ssrf_path_with_fragment_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject a path that embeds a fragment."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="must not include query parameters"):
        client.build_url("/api/dcim/devices/#frag")


def test_ssrf_empty_path_rejected(tmp_path, monkeypatch) -> None:
    """build_url must reject an empty or whitespace-only path."""
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(ValueError):
        client.build_url("")
    with pytest.raises(ValueError):
        client.build_url("   ")


# ---------------------------------------------------------------------------
# Path traversal in request paths
# ---------------------------------------------------------------------------

def test_path_traversal_stays_within_base_url(tmp_path, monkeypatch) -> None:
    """../../etc/passwd in a request path must resolve under the base URL."""
    client = _client(tmp_path, monkeypatch)
    # ../.. traversal in a relative path is a plain-path component — no scheme/netloc
    # so build_url accepts it and urljoin handles it. The result must still start
    # with the configured base URL's host, not escape to a different origin.
    url = client.build_url("/api/../../etc/passwd")
    assert "netbox.example.com" in url
    assert "evil" not in url


def test_encoded_path_traversal_preserved_as_literal(tmp_path, monkeypatch) -> None:
    """Percent-encoded traversal must be treated as a literal path component.
    urlsplit does not decode percent-encoding, so %2e%2e%2f is a valid path
    string that build_url accepts. The resulting URL must remain under the base.
    """
    client = _client(tmp_path, monkeypatch)
    url = client.build_url("/api/%2e%2e%2fetc%2fpasswd")
    assert "netbox.example.com" in url


# ---------------------------------------------------------------------------
# Base URL injection via normalize_base_url
# ---------------------------------------------------------------------------

def test_base_url_rejects_javascript_scheme() -> None:
    with pytest.raises(ValueError, match="http or https"):
        normalize_base_url("javascript:alert(1)")


def test_base_url_rejects_data_scheme() -> None:
    with pytest.raises(ValueError, match="http or https"):
        normalize_base_url("data:text/html,<script>alert(1)</script>")


def test_base_url_rejects_ftp_scheme() -> None:
    with pytest.raises(ValueError, match="http or https"):
        normalize_base_url("ftp://netbox.example.com")


def test_base_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="embedded credentials"):
        normalize_base_url("https://user:pass@netbox.example.com")


def test_base_url_rejects_query_string() -> None:
    with pytest.raises(ValueError, match="query parameters or fragments"):
        normalize_base_url("https://netbox.example.com/?inject=1")


def test_base_url_rejects_fragment() -> None:
    with pytest.raises(ValueError, match="query parameters or fragments"):
        normalize_base_url("https://netbox.example.com/#frag")


def test_base_url_embedded_newline_rejected_or_normalized() -> None:
    """A base URL containing a newline is not a valid HTTP scheme URL and must
    be rejected. Newlines could enable header injection in some HTTP clients."""
    with pytest.raises((ValueError, Exception)):
        normalize_base_url("https://netbox.example.com\r\nX-Injected: evil")


def test_base_url_null_byte_rejected_or_normalized() -> None:
    """A base URL containing a null byte must be rejected or produce a URL
    without the null byte so it cannot poison downstream HTTP headers."""
    result_or_error: str | None = None
    try:
        result_or_error = normalize_base_url("https://netbox.example.com\x00evil")
    except (ValueError, Exception):
        return  # rejection is the correct outcome
    # If it didn't raise, the null byte must not appear in the result
    assert "\x00" not in (result_or_error or "")


# ---------------------------------------------------------------------------
# Cache key isolation
# ---------------------------------------------------------------------------

def test_cache_key_differs_for_different_auth_tokens() -> None:
    """Two identical requests that differ only in Authorization header must
    produce different cache keys so one user's cached data is not served to
    another user's session."""
    key_a = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token aaaa",
    )
    key_b = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token bbbb",
    )
    assert key_a != key_b


def test_cache_key_differs_for_different_base_urls() -> None:
    """Same path on two different NetBox instances must produce different cache keys."""
    key_a = build_cache_key(
        base_url="https://netbox-prod.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token t",
    )
    key_b = build_cache_key(
        base_url="https://netbox-dev.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token t",
    )
    assert key_a != key_b


def test_cache_key_same_for_identical_requests() -> None:
    """Identical requests must produce the same cache key (deterministic)."""
    kwargs = dict(
        base_url="https://netbox.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token t",
    )
    assert build_cache_key(**kwargs) == build_cache_key(**kwargs)


def test_cache_key_unauthenticated_differs_from_authenticated() -> None:
    """A request with no authorization header must not share a cache entry
    with an authenticated request for the same path."""
    key_authed = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization="Token secret",
    )
    key_anon = build_cache_key(
        base_url="https://netbox.example.com",
        method="GET",
        path="/api/dcim/devices/",
        query=None,
        authorization=None,
    )
    assert key_authed != key_anon


# ---------------------------------------------------------------------------
# HTTP header injection via token value
# ---------------------------------------------------------------------------

def test_newline_in_v1_token_does_not_inject_header_lines() -> None:
    """A token_secret containing CR+LF must not produce a multi-line
    Authorization header value. The returned string must be a single line."""
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="validtoken\r\nX-Injected: evil",
    )
    header = authorization_header_value(cfg)
    assert "\r" not in header
    assert "\n" not in header


def test_newline_in_v2_token_key_does_not_inject_header_lines() -> None:
    """A token_key containing a newline must not produce a multi-line header."""
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v2",
        token_key="key\r\nX-Injected: evil",
        token_secret="secret",
    )
    header = authorization_header_value(cfg)
    assert "\r" not in header
    assert "\n" not in header


# ---------------------------------------------------------------------------
# Credential representation
# ---------------------------------------------------------------------------

def test_config_token_secret_field_coerces_whitespace_to_none() -> None:
    """A token_secret that is purely whitespace is treated as absent,
    preventing accidental use of a blank token."""
    cfg = Config(base_url="https://netbox.example.com", token_secret="   ")
    assert cfg.token_secret is None


def test_config_base_url_strips_trailing_slashes() -> None:
    """Trailing slashes in base_url must be normalized away so request path
    joining is deterministic and cannot introduce double-slash sequences."""
    cfg = Config(base_url="https://netbox.example.com/")
    assert cfg.base_url is not None
    # Should not end with /
    assert not cfg.base_url.endswith("/") or cfg.base_url == "https://netbox.example.com"
