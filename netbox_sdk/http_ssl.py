"""HTTPS connector helpers and TLS failure detection for the aiohttp client."""

from __future__ import annotations

import ssl
from typing import Any
from urllib.parse import urlsplit

from netbox_sdk.config import Config


def connector_for_config(cfg: Config) -> Any | None:
    """Return an aiohttp TCPConnector for HTTPS, or None to use ClientSession defaults.

    For ``https`` URLs: when ``ssl_verify`` is ``False``, returns a connector with
    verification disabled. Otherwise returns ``None`` (library default: verify).
    For ``http`` URLs, returns ``None``.
    """
    base = cfg.base_url or ""
    parsed = urlsplit(base)
    if parsed.scheme.lower() != "https":
        return None
    if cfg.ssl_verify is False:
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc

        return aiohttp.TCPConnector(ssl=False)
    return None


def is_certificate_verify_failure(exc: BaseException) -> bool:
    """True if ``exc`` (or its cause chain) indicates TLS certificate verification failed."""
    cur: BaseException | None = exc
    seen: set[int] = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        if isinstance(cur, ssl.SSLCertVerificationError):
            return True
        try:
            import aiohttp

            if isinstance(cur, aiohttp.ClientConnectorCertificateError):
                return True
            if isinstance(cur, aiohttp.ClientSSLError):
                if _text_suggests_cert_verify_failure(str(cur)):
                    return True
        except Exception:
            pass
        if _text_suggests_cert_verify_failure(str(cur)):
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def is_certificate_verify_failure_text(text: str | None) -> bool:
    """True if a connection error string describes certificate verification failure."""
    return _text_suggests_cert_verify_failure(text or "")


def _text_suggests_cert_verify_failure(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    return (
        "certificate verify failed" in lower
        or "sslcertverificationerror" in lower
        or "cert_verify_failed" in lower
    )
