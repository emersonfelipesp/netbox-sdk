"""Data models and HTTP client logic for authenticated NetBox API requests.

Security considerations:
- Authorization headers are constructed from sanitized token values
- Request paths must be relative to base URL (no SSRF via absolute URLs)
- Query parameters and fragments are rejected in request paths
- TLS certificate verification can be disabled via ssl_verify=False (logged at WARNING)
- HTTP cache entries use private file permissions (0o600)
- Cache keys are SHA-256 fingerprints, never raw tokens or credentials
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import posixpath
import re
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any, TypeAlias
from urllib.parse import urljoin, urlsplit

from pydantic import BaseModel, ConfigDict, Field

from netbox_sdk.config import (
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    authorization_header_value,
    cache_dir,
    load_profile_config,
)
from netbox_sdk.exceptions import RequestError
from netbox_sdk.http_cache import (
    CacheEntry,
    CachePolicy,
    HttpCacheStore,
    QueryParams,
    build_cache_key,
)
from netbox_sdk.http_ssl import connector_for_config
from netbox_sdk.telemetry import client_request_span, server_address_from_url

if TYPE_CHECKING:
    import aiohttp

logger = logging.getLogger(__name__)

_ENCODED_PATH_SEPARATOR_RE = re.compile(r"%(?:2f|5c)", re.IGNORECASE)

JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
FileLike: TypeAlias = IO[bytes] | IO[str]

# Per-task scoped request headers. Using a ContextVar (rather than a mutable
# instance attribute) makes header_scope() / activate_branch() safe under
# asyncio.gather: each Task copies the current context at creation, so a
# .set() in one task is invisible to siblings, and .reset() restores the
# token without races on shared state. The default is None (treated as empty)
# so no shared mutable dict is ever exposed to readers.
_scoped_headers: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "netbox_sdk_scoped_headers", default=None
)


def _extract_case_insensitive(
    headers: dict[str, str], name: str
) -> tuple[str | None, dict[str, str]]:
    """Pop every case variant of header ``name`` from ``headers``.

    Returns the value of the last matching key encountered in ``headers``'
    own iteration order and a new dict with all matching keys removed.
    Plain dicts are case-sensitive, but HTTP header names are not, so
    without this a caller-supplied "authorization" and a configured
    "Authorization" would be treated as two independent headers instead of
    one overriding the other.

    Callers that layer multiple precedence sources together (e.g.
    persistent < scoped < per-call) must call this once per source *before*
    merging the sources into a single dict, then resolve precedence
    explicitly among the returned values — never by merging first and
    extracting from the combined dict. A plain dict's ``update()`` does not
    reorder an existing key when a same-named-but-differently-cased header
    from a later, higher-precedence source is applied; it only appends
    genuinely new keys at the end. So a combined dict built from persistent
    ``{"Authorization": ...}`` then scoped ``{"authorization": ...}`` would
    put the scoped key last in iteration order and make it win here even
    over a same-cased per-call ``"Authorization"`` that was supposed to
    take precedence over both.
    """
    target = name.lower()
    value: str | None = None
    remaining: dict[str, str] = {}
    for key, header_value in headers.items():
        if key.lower() == target:
            value = header_value
        else:
            remaining[key] = header_value
    return value, remaining


# NetBox "detail action" endpoints (see netbox_sdk.facade.DETAIL_ENDPOINT_SPECS)
# whose writes create objects in an entirely different collection than the
# endpoint's own path or its immediate parent detail path. For example,
# POST /api/ipam/prefixes/{id}/available-ips/ creates IPAddress rows that
# live under /api/ipam/ip-addresses/, not anything under
# /api/ipam/prefixes/. The default _related_cache_paths() derivation (exact
# path + immediate parent detail path) never touches the collection these
# actions actually populate, so a cached list/filter read of that
# collection would keep serving pre-write data until it naturally expired.
# Keyed by the action's trailing path segment since that alone is enough to
# disambiguate among the handful of mutating actions NetBox exposes today;
# read-only actions (napalm, trace, units, elevation, paths) are omitted
# since a GET never stales anything.
_ACTION_CROSS_RESOURCE_CACHE_PATHS: dict[str, tuple[str, ...]] = {
    # ASNRange.asn_count changes with the allocated ASN as well.
    "available-asns": ("/api/ipam/asns/", "/api/ipam/asn-ranges/"),
    # Prefix/IPRange serializers expose no affected utilization/count field.
    "available-ips": ("/api/ipam/ip-addresses/",),
    # This collection is both the allocation target and the parent collection
    # whose Prefix.children field changes.
    "available-prefixes": ("/api/ipam/prefixes/",),
    # VLANGroup.vlan_count/utilization change with the allocated VLAN as well.
    "available-vlans": ("/api/ipam/vlans/", "/api/ipam/vlan-groups/"),
}


class ApiResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: int
    text: str
    headers: dict[str, str] = Field(default_factory=dict)

    def json(self) -> JSONValue:  # ty: ignore[invalid-method-override]
        """Parse the response body as JSON (scalar, object, or array)."""
        return json.loads(self.text)


class ConnectionProbe(BaseModel):
    status: int
    version: str
    ok: bool
    error: str | None = None


class NetBoxApiClient:
    """Async NetBox REST client with connection pooling and lifecycle management.

    Thread Safety:
        This class is NOT thread-safe. Use one client instance per coroutine/event loop.
        For multi-threaded code, create separate client instances per thread, or use
        proper synchronization.

    Usage:
        # Context manager (recommended):
        async with NetBoxApiClient(config) as client:
            response = await client.request("GET", "/api/dcim/devices/")

        # Manual lifecycle:
        client = NetBoxApiClient(config)
        try:
            response = await client.request("GET", "/api/dcim/devices/")
        finally:
            await client.close()

        # Connection reuse (automatic):
        client = NetBoxApiClient(config)
        # Multiple requests reuse the same underlying aiohttp.ClientSession
        await client.request("GET", "/api/dcim/devices/")
        await client.request("GET", "/api/ipam/ip-addresses/")
        await client.close()

    Note:
        Sessions are created lazily on first request and reused across subsequent requests.
        Use the `session_active` property to check if a session exists.
    """

    def __init__(
        self,
        config: Config,
        *,
        on_token_refresh: Callable[[Config], tuple[str | None, Config] | str | None] | None = None,
    ) -> None:
        self.config = config
        self._cache = HttpCacheStore(cache_dir())
        self._on_token_refresh = on_token_refresh or self._default_token_refresh_callback()
        self._openapi_cache: dict[str, JSONValue] | None = None
        self._session: aiohttp.ClientSession | None = None
        self._session_loop_id: int | None = None
        self._session_lock: asyncio.Lock | None = None
        self._context_depth: int = 0
        # Long-lived header overrides applied to every request, regardless of
        # the calling task's :data:`_scoped_headers` snapshot. Used by the
        # TUI to keep ``X-NetBox-Branch`` set across background workers when
        # the user activates a branch.
        self.persistent_headers: dict[str, str] = {}
        logger.debug("initialized api client for %s", self.config.base_url or "<unset>")
        bu = self.config.base_url or ""
        if bu and urlsplit(bu).scheme.lower() == "https" and self.config.ssl_verify is False:
            logger.warning("HTTPS TLS certificate verification is disabled for %s", bu)

    def _default_token_refresh_callback(
        self,
    ) -> Callable[[Config], tuple[str | None, Config] | str | None] | None:
        if self.config.base_url != DEMO_BASE_URL:
            return None

        def _refresh(config: Config) -> tuple[str | None, Config]:
            from netbox_sdk.demo_auth import refresh_demo_profile

            refreshed = refresh_demo_profile(config, headless=True)
            return authorization_header_value(refreshed), refreshed

        return _refresh

    def _get_lock(self) -> asyncio.Lock:
        """Get or create the session lock (must be called from async context)."""
        if self._session_lock is None:
            self._session_lock = asyncio.Lock()
        return self._session_lock

    def _session_closed(self) -> bool:
        """Return True when the current session is closed.

        Some test doubles emulate only the subset of aiohttp.ClientSession used
        by request execution and do not expose ``closed``.
        """
        if self._session is None:
            return True
        return bool(getattr(self._session, "closed", False))

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a reusable aiohttp session with connection pooling.

        Thread-safe via internal lock. If the session was created for a different
        event loop, it is closed and a new one is created.
        """
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc

        current_loop_id = id(asyncio.get_running_loop())

        # Fast path: session already valid for this loop — no lock needed
        if (
            self._session is not None
            and not self._session_closed()
            and self._session_loop_id == current_loop_id
        ):
            return self._session

        async with self._get_lock():
            # Re-check under lock in case another coroutine just created the session
            session_closed = self._session_closed()
            if self._session is None or session_closed or self._session_loop_id != current_loop_id:
                if self._session is not None and not session_closed:
                    await self._session.close()
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                connector = connector_for_config(self.config)
                session_kwargs: dict[str, Any] = {"timeout": timeout}
                if connector is not None:
                    session_kwargs["connector"] = connector
                self._session = aiohttp.ClientSession(**session_kwargs)
                self._session_loop_id = current_loop_id

            return self._session

    async def close(self) -> None:
        """Close the underlying HTTP session and release resources."""
        async with self._get_lock():
            if self._session is not None and not self._session_closed():
                await self._session.close()
            self._session = None
            self._session_loop_id = None
            self._openapi_cache = None

    async def reset_session(self) -> None:
        """Force close and recreate the session on next request."""
        await self.close()

    @property
    def session_active(self) -> bool:
        """Return True if a session exists and is not closed."""
        return self._session is not None and not self._session_closed()

    @property
    def current_loop_id(self) -> int | None:
        """Return the event loop ID the session was created for, if any."""
        return self._session_loop_id

    async def __aenter__(self) -> NetBoxApiClient:
        self._context_depth += 1
        return self

    async def __aexit__(self, *args: object) -> None:
        self._context_depth -= 1
        if self._context_depth == 0:
            await self.close()

    def build_url(self, path: str) -> str:
        if not self.config.base_url:
            raise RuntimeError("NetBox base URL is not configured")
        normalized = self._normalize_request_path(path)
        return urljoin(f"{self.config.base_url.rstrip('/')}/", normalized.lstrip("/"))

    def _normalize_request_path(self, path: str) -> str:
        raw = path.strip()
        if not raw:
            raise ValueError("Request path cannot be empty")
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc:
            raise ValueError("Request path must be relative to the configured NetBox base URL")
        if parsed.query or parsed.fragment:
            raise ValueError("Request path must not include query parameters or fragments")
        if _ENCODED_PATH_SEPARATOR_RE.search(parsed.path):
            raise ValueError(
                "Request path must not contain percent-encoded path separators (%2F or %5C)"
            )
        normalized = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
        # Collapse repeated "/" the same way the outbound request's own
        # build_url() already does, so the path used for cache keys, the
        # cache-generation fence, and invalidate_path() can never diverge
        # from what is actually sent on the wire. build_url() always strips
        # every leading "/" before merging the path onto the base URL via
        # urljoin(), and that merge collapses internal "//" runs down to a
        # single "/" even when neither segment is a literal "." or "..".
        # This runs unconditionally, not only when a dot segment is present:
        # left unresolved, a request through an equivalent-but-unnormalized
        # alias (e.g. "/api//dcim/devices/5/") mutated the canonical
        # resource on the wire while invalidating cache entries keyed to the
        # literal alias instead — the canonical cached entries stayed
        # untouched and a verification read could still return stale
        # pre-write data. urlsplit() above already rejects a leading "//" as
        # a netloc, so `normalized` is always exactly one leading "/" here —
        # posixpath's POSIX-mandated special case for exactly two leading
        # slashes never applies.
        had_trailing_slash = normalized.endswith("/") and normalized != "/"
        resolved = posixpath.normpath(normalized)
        if had_trailing_slash and not resolved.endswith("/"):
            resolved += "/"
        normalized = resolved
        # aiohttp builds its outbound request from the URL string this
        # module hands it via yarl.URL(str), which fully canonicalizes the
        # path exactly like a browser would: it resolves any remaining
        # "."/".." segments AND percent-decodes every octet that encodes an
        # RFC 3986 "unreserved" character (e.g. "%64cim" -> "dcim",
        # "device%73" -> "devices"), while leaving encoded reserved
        # delimiters such as "%3F"/"%23" untouched. Encoded path separators
        # are rejected above because servers and proxies disagree on whether
        # to decode them before route matching. The dot-segment-only
        # handling this function used to do did not decode non-dot aliases
        # at all, so a write through e.g. "/api/%64cim/devices/5/" mutated
        # the canonical "/api/dcim/devices/5/" resource on the wire while
        # invalidating cache entries keyed to the literal encoded alias,
        # leaving the canonical cached entries stale and servable by a
        # verification read. Delegating to yarl's own ``raw_path`` reproduces
        # aiohttp's canonicalization exactly rather than
        # re-implementing RFC 3986's unreserved-character set by hand — the
        # host portion is a fixed placeholder because path canonicalization
        # does not depend on it.
        try:
            from yarl import URL
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc
        had_trailing_slash = normalized.endswith("/") and normalized != "/"
        canonical = URL(f"http://netbox-sdk.invalid{normalized}").raw_path
        if had_trailing_slash and not canonical.endswith("/"):
            canonical += "/"
        return canonical

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> ApiResponse:
        with client_request_span(
            self.config,
            method,
            path,
            server_address_from_url(self.config.base_url),
        ) as span:
            response = await self._request_impl(
                method=method,
                path=path,
                query=query,
                payload=payload,
                headers=headers,
                expect_json=expect_json,
            )
            span.set_response_status(response.status)
            span.set_cache_status(response.headers.get("X-NBX-Cache"))
            return response

    async def stream_sse(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[str]:
        """Stream raw Server-Sent Event blocks from a NetBox-relative path.

        This intentionally bypasses the normal request stack: streamed responses
        cannot be cached or replayed for token fallback/retry behavior.
        """
        path = self._normalize_request_path(path)
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc

        authorization = authorization_header_value(self.config)
        # Extract Authorization from each layer *before* merging the rest of
        # the headers together, and resolve precedence explicitly rather
        # than by relying on dict iteration order after the merge: a plain
        # dict does not reorder a pre-existing key when update() applies a
        # same-named-but-differently-cased header from a higher-precedence
        # layer, it only appends genuinely new keys at the end. So merging
        # persistent {"Authorization": ...} then scoped {"authorization":
        # ...} would leave the scoped key last in iteration order and make
        # it win even over a later same-cased per-call "Authorization" that
        # was supposed to take precedence over both, letting a read or
        # mutation intended for the explicit per-call token execute under a
        # different caller's credential instead.
        persistent = dict(self.persistent_headers)
        persistent_authorization, persistent = _extract_case_insensitive(
            persistent, "Authorization"
        )
        scoped = dict(_scoped_headers.get() or {})
        scoped_authorization, scoped = _extract_case_insensitive(scoped, "Authorization")
        call_headers = dict(headers or {})
        call_authorization, call_headers = _extract_case_insensitive(call_headers, "Authorization")
        req_headers = dict(persistent)
        req_headers.update(scoped)
        req_headers.update(call_headers)
        req_headers.setdefault("Accept", "text/event-stream")
        caller_authorization = (
            call_authorization or scoped_authorization or persistent_authorization
        )
        effective_authorization = caller_authorization or authorization
        if effective_authorization:
            req_headers["Authorization"] = effective_authorization

        stream_timeout = 7200.0 if timeout is None else timeout
        request_timeout = aiohttp.ClientTimeout(total=stream_timeout, sock_read=None)
        session = await self._get_session()
        async with session.request(
            method=method.upper(),
            url=self.build_url(path),
            params=query,
            json=payload,
            headers=req_headers,
            timeout=request_timeout,
            # A redirect to a 200 HTML page (e.g. a login/interstitial) must not be
            # followed and then parsed as SSE — surface it as an error instead.
            allow_redirects=False,
        ) as response:
            if response.status >= 400:
                text = await response.text()
                snippet = text[:1000]
                raise RequestError(
                    ApiResponse(
                        status=response.status,
                        text=(f"SSE stream request failed with HTTP {response.status}: {snippet}"),
                        headers=dict(response.headers),
                    )
                )

            # Guard against a non-SSE success/redirect body being silently parsed
            # as an empty event stream (which would yield no frames and no error).
            # A 3xx (redirect, not followed above) or any 2xx whose Content-Type is
            # not ``text/event-stream`` is a broken stream, not valid SSE.
            content_type = response.headers.get("Content-Type", "")
            if response.status >= 300 or "text/event-stream" not in content_type.lower():
                text = await response.text()
                snippet = text[:1000]
                raise RequestError(
                    ApiResponse(
                        status=response.status,
                        text=(
                            "SSE stream request did not return an event stream "
                            f"(HTTP {response.status}, Content-Type "
                            f"{content_type or '<none>'!r}): {snippet}"
                        ),
                        headers=dict(response.headers),
                    )
                )

            buffer = ""
            async for raw in response.content:
                buffer += raw.decode("utf-8", errors="replace")
                while True:
                    block, buffer = self._pop_sse_block(buffer)
                    if block is None:
                        break
                    if block.strip():
                        yield block
            if buffer.strip():
                yield buffer

    @staticmethod
    def _pop_sse_block(buffer: str) -> tuple[str | None, str]:
        candidates = [
            (idx, marker) for marker in ("\n\n", "\r\n\r\n") if (idx := buffer.find(marker)) >= 0
        ]
        if not candidates:
            return None, buffer
        index, marker = min(candidates, key=lambda item: item[0])
        return buffer[:index], buffer[index + len(marker) :]

    async def _request_impl(
        self,
        method: str,
        path: str,
        *,
        query: QueryParams | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> ApiResponse:
        # Canonicalize once, up front, so the cache key, the cache-generation
        # fence, invalidate_path(), and the outbound request all agree on the
        # same path — build_url() below would otherwise silently resolve an
        # unnormalized alias (e.g. "/api/dcim/../ipam/prefixes/") to its
        # canonical form only for the wire request, leaving every
        # cache-related lookup keyed to the literal, never-cached alias.
        path = self._normalize_request_path(path)
        authorization = authorization_header_value(self.config)
        cache_policy = self._cache_policy(
            method=method,
            path=path,
            query=query,
            payload=payload,
        )
        logger.info(
            "api request starting",
            extra={
                "http_method": method.upper(),
                "request_path": path,
                "query_keys": sorted((query or {}).keys()),
                "has_payload": payload is not None,
            },
        )
        cache_key: str | None = None
        cache_entry = None
        cache_generation: int | None = None
        # Header precedence (lowest → highest): persistent_headers (client-wide,
        # e.g. the TUI's active branch) < _scoped_headers (per-task header_scope,
        # e.g. SDK ``activate``/``activate_branch``) < per-call ``headers``. A
        # task-scoped branch therefore overrides a client-wide one for the
        # duration of its with-block, then falls back to the persistent value.
        #
        # HTTP header names are case-insensitive, but a plain dict is not: a
        # caller-supplied "authorization" or "AUTHORIZATION" header would
        # otherwise sit alongside "Authorization" as a distinct dict key,
        # never be picked up by an exact-case lookup, and so be sent to
        # NetBox with the real credential while cached under the
        # configured/anonymous identity instead — letting a later anonymous
        # or differently-cased read hit that cache entry. Extracting
        # Authorization from each layer *before* merging (rather than
        # merging first and extracting the "last" match from the combined
        # dict) also matters for precedence, not just deduplication: a plain
        # dict does not reorder a pre-existing key when update() applies a
        # same-named-but-differently-cased header from a higher-precedence
        # layer, it only appends genuinely new keys at the end. Merging
        # persistent {"Authorization": ...} then scoped {"authorization":
        # ...} would leave the scoped key last in iteration order and make
        # it win even over a later same-cased per-call "Authorization" that
        # was supposed to take precedence over both, letting a read or
        # mutation intended for the explicit per-call token execute under a
        # different caller's credential instead.
        persistent = dict(self.persistent_headers)
        persistent_authorization, persistent = _extract_case_insensitive(
            persistent, "Authorization"
        )
        scoped = dict(_scoped_headers.get() or {})
        scoped_authorization, scoped = _extract_case_insensitive(scoped, "Authorization")
        call_headers = dict(headers or {})
        call_authorization, call_headers = _extract_case_insensitive(call_headers, "Authorization")
        req_headers = dict(persistent)
        req_headers.update(scoped)
        req_headers.update(call_headers)
        # A per-call bearer (e.g. MCP's persistent_headers override for a
        # forwarded caller token) must scope the cache key too, or requests
        # made under different tokens collide on the same cached response.
        caller_authorization = (
            call_authorization or scoped_authorization or persistent_authorization
        )
        effective_authorization = caller_authorization or authorization
        # Any other header that can change the response representation (e.g.
        # X-NetBox-Branch) must scope the cache key too, or a same-token read
        # in one NetBox Branching schema can serve a response cached from a
        # different schema without ever contacting NetBox. req_headers no
        # longer contains any Authorization variant, so it can be used as-is.
        scope_headers = dict(req_headers)
        # Restore exactly one canonically-cased Authorization header now that
        # every case variant has been resolved, so req_headers stays a normal
        # single-source-of-truth headers dict for downstream callers.
        if effective_authorization:
            req_headers["Authorization"] = effective_authorization
        if cache_policy is not None and self.config.base_url:
            cache_key = build_cache_key(
                base_url=self.config.base_url,
                method=method,
                path=path,
                query=query,
                authorization=effective_authorization,
                scope_headers=scope_headers,
            )
            # Captured before the request is issued so a concurrent write's
            # invalidate_path() that lands while this GET is in flight is
            # detected at save time below, instead of this now-stale response
            # silently repopulating the cache after the write already purged it.
            cache_generation = self._cache.path_generation(path)
            cache_entry = self._cache.load(cache_key)
            if cache_entry is not None and cache_entry.is_fresh(self._now()):
                return self._cached_response(cache_entry, cache_status="HIT")
            if cache_entry is not None:
                if cache_entry.etag:
                    req_headers.setdefault("If-None-Match", cache_entry.etag)
                if cache_entry.last_modified:
                    req_headers.setdefault("If-Modified-Since", cache_entry.last_modified)

        session = await self._get_session()
        req_kwargs: dict[str, Any] = dict(
            method=method,
            path=path,
            query=query,
            payload=payload,
            headers=req_headers,
            expect_json=expect_json,
        )
        is_write_method = method.upper() not in {"GET", "HEAD"}
        try:
            response = await self._request_once(
                session, authorization=effective_authorization, **req_kwargs
            )
            # These fallbacks retry using the client's own configured credential
            # (or a refreshed one from the token-refresh callback), which is a
            # different identity than a caller-supplied override. If a caller
            # provided its own Authorization header, an invalid/foreign
            # credential must never silently succeed by falling back to the
            # SDK's configured account — that would both perform the request
            # under the wrong identity and, for GET requests, cache the
            # configured account's response under the cache key computed from
            # the caller's (rejected) credential, serving it back to that
            # caller or anyone else presenting the same override later.
            if caller_authorization is None and self._should_retry_with_v1(response):
                response = await self._request_once(
                    session, authorization=self._v1_fallback_header(), **req_kwargs
                )
            elif caller_authorization is None and self._should_refresh_demo_v1_token(response):
                authorization = self._refresh_demo_v1_authorization()
                if authorization:
                    response = await self._request_once(
                        session, authorization=authorization, **req_kwargs
                    )
            if (
                response.status == 304
                and cache_entry is not None
                and cache_generation is not None
                and self._cache.path_generation(path) != cache_generation
            ):
                # A concurrent write invalidated this path while our
                # conditional request was in flight. The 304 only confirms
                # the representation matched the ETag/Last-Modified we sent
                # from the pre-write entry, which we can no longer trust —
                # refetch unconditionally instead of letting the
                # generation-fenced refresh() below resurrect stale data.
                unconditional_headers = dict(req_headers)
                unconditional_headers.pop("If-None-Match", None)
                unconditional_headers.pop("If-Modified-Since", None)
                # Captured before the replacement request is issued, exactly
                # like the initial cache_generation capture above — if a
                # second concurrent write invalidates the path while this
                # unconditional request is in flight, the fenced save/refresh
                # below must see that mismatch and skip persisting, not adopt
                # a post-response generation that would make the now-stale
                # replacement response pass the fence as if it were current.
                cache_generation = self._cache.path_generation(path)
                response = await self._request_once(
                    session,
                    authorization=effective_authorization,
                    method=method,
                    path=path,
                    query=query,
                    payload=payload,
                    headers=unconditional_headers,
                    expect_json=expect_json,
                )
        except Exception:
            logger.exception(
                "api request failed",
                extra={"http_method": method.upper(), "request_path": path},
            )
            if is_write_method:
                # NetBox may have committed the write server-side even
                # though we never received a definitive response (e.g. the
                # connection dropped mid-read). Purge related cache entries
                # defensively so a verification read can't serve the stale
                # pre-write data as if the write never happened.
                self._safe_invalidate_related_cache(path, payload)
            if cache_entry is not None and cache_entry.can_serve_stale(self._now()):
                return self._cached_response(cache_entry, cache_status="STALE")
            raise
        logger.info(
            "api request completed",
            extra={
                "http_method": method.upper(),
                "request_path": path,
                "status": response.status,
            },
        )
        if is_write_method:
            # Invalidate regardless of response status, not only on 2xx: a
            # plugin or raw endpoint can commit the mutation and then return
            # a non-2xx status during post-commit processing (e.g. a 500 from
            # signal/webhook handling after the row was written). Restricting
            # this to confirmed success left that committed write invisible
            # to the cache, so a verification read could still return the
            # stale pre-write entry and encourage an unsafe duplicate retry.
            self._safe_invalidate_related_cache(path, payload)
        return self._finalize_cached_response(
            response=response,
            cache_key=cache_key,
            cache_entry=cache_entry,
            cache_policy=cache_policy,
            path=path,
            cache_generation=cache_generation,
        )

    async def _request_once(
        self,
        session: aiohttp.ClientSession,
        *,
        method: str,
        path: str,
        query: QueryParams | None,
        payload: dict[str, Any] | list[Any] | None,
        headers: dict[str, str] | None,
        authorization: str | None,
        expect_json: bool,
    ) -> ApiResponse:
        files_payload = None
        json_payload = payload
        req_headers = dict(headers or {})
        req_headers.setdefault("Accept", "application/json" if expect_json else "*/*")
        if authorization:
            req_headers["Authorization"] = authorization
        if isinstance(payload, dict):
            json_payload, files_payload = self._extract_files(payload)

        async with session.request(
            method=method.upper(),
            url=self.build_url(path),
            params=query,
            json=json_payload if files_payload is None else None,
            data=files_payload if files_payload is not None else None,
            headers=req_headers,
        ) as response:
            text = await response.text()
            logger.debug(
                "received raw api response",
                extra={
                    "http_method": method.upper(),
                    "request_path": path,
                    "status": response.status,
                },
            )
            return ApiResponse(status=response.status, text=text, headers=dict(response.headers))

    def _extract_files(self, payload: dict[str, Any]) -> tuple[dict[str, Any], Any | None]:
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc

        clean_payload: dict[str, Any] = {}
        form: Any | None = None
        for key, value in payload.items():
            file_info = self._coerce_file_field(value, field_name=key)
            if file_info is None:
                clean_payload[key] = value
                continue
            if form is None:
                form = aiohttp.FormData()
            filename, file_obj, content_type = file_info
            form.add_field(key, file_obj, filename=filename, content_type=content_type)

        if form is None:
            return payload, None

        for key, value in clean_payload.items():
            if isinstance(value, bool):
                form.add_field(key, json.dumps(value))
            elif value is None:
                form.add_field(key, "")
            elif isinstance(value, (dict, list)):
                form.add_field(key, json.dumps(value))
            else:
                form.add_field(key, str(value))
        return clean_payload, form

    def _coerce_file_field(
        self, value: object, *, field_name: str
    ) -> tuple[str, FileLike, str | None] | None:
        if self._is_file_like(value):
            return self._file_tuple(getattr(value, "name", field_name), value, None)
        if isinstance(value, tuple) and len(value) >= 2 and self._is_file_like(value[1]):
            filename = value[0]
            file_obj = value[1]
            content_type = value[2] if len(value) > 2 else None
            return self._file_tuple(filename, file_obj, content_type)
        return None

    def _file_tuple(
        self, filename: object, file_obj: FileLike, content_type: object
    ) -> tuple[str, FileLike, str | None]:
        name = Path(str(filename)).name if filename else "upload"
        return name, file_obj, str(content_type) if content_type else None

    def _is_file_like(self, value: object) -> bool:
        if isinstance(value, (str, bytes, bytearray)):
            return False
        return hasattr(value, "read") and callable(getattr(value, "read"))

    def _v1_fallback_header(self) -> str | None:
        if not self.config.token_secret:
            return None
        return f"Token {self.config.token_secret}"

    def _should_retry_with_v1(self, response: ApiResponse) -> bool:
        if self.config.token_version != "v2" or not self.config.token_secret:
            return False
        if response.status not in {401, 403}:
            return False
        return "invalid v2 token" in response.text.lower()

    def _should_refresh_demo_v1_token(self, response: ApiResponse) -> bool:
        if self.config.base_url != DEMO_BASE_URL:
            return False
        if self.config.token_version != "v1":
            return False
        if response.status not in {401, 403}:
            return False
        if "invalid v1 token" not in response.text.lower():
            return False
        if self.config.demo_username and self.config.demo_password:
            return True
        refreshed_profile = load_profile_config(DEMO_PROFILE)
        if refreshed_profile.demo_username and refreshed_profile.demo_password:
            updates: dict[str, Any] = {
                "demo_username": refreshed_profile.demo_username,
                "demo_password": refreshed_profile.demo_password,
            }
            if refreshed_profile.timeout:
                updates["timeout"] = refreshed_profile.timeout
            self.config = self.config.model_copy(update=updates)
            return True
        return False

    def _refresh_demo_v1_authorization(self) -> str | None:
        if self._on_token_refresh is None:
            logger.debug("no token refresh callback configured; skipping demo token refresh")
            return None
        try:
            result = self._on_token_refresh(self.config)
        except Exception:
            logger.exception("token refresh callback failed")
            return None
        if isinstance(result, tuple):
            authorization, updated_config = result
            self.config = updated_config
            return authorization
        return result

    def _cache_policy(
        self,
        *,
        method: str,
        path: str,
        query: QueryParams | None,
        payload: dict[str, Any] | list[Any] | None,
    ) -> CachePolicy | None:
        if method.upper() != "GET" or payload is not None:
            return None
        if not path.startswith("/api/"):
            return None
        if path == "/api/status/":
            return None
        # netbox-branching state mutates via background jobs; caching would
        # mask sync/merge/revert progress. Skip plugin sub-paths and the
        # core jobs polling endpoint. The feature-detection root is included
        # in the exclusion for predictability across short-lived test runs.
        if path.startswith("/api/plugins/branching/"):
            return None
        if path.startswith("/api/core/jobs/"):
            return None
        if self._is_list_request(path):
            return CachePolicy(fresh_ttl_seconds=60.0, stale_if_error_seconds=300.0)
        if query:
            return CachePolicy(fresh_ttl_seconds=30.0, stale_if_error_seconds=120.0)
        return CachePolicy(fresh_ttl_seconds=15.0, stale_if_error_seconds=60.0)

    def _is_list_request(self, path: str) -> bool:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 3:
            return False
        return parts[0] == "api"

    def _collection_path_for(self, path: str) -> str | None:
        """Derive the containing list path for a detail path, if any.

        ``/api/dcim/devices/5/`` -> ``/api/dcim/devices/``. Used to purge the
        collection's cached list/filter responses whenever a single object
        underneath it is written.
        """
        parts = [part for part in path.split("/") if part]
        if len(parts) < 2:
            return None
        return "/" + "/".join(parts[:-1]) + "/"

    def _trailing_action_name(self, path: str) -> str | None:
        """Return the action segment of a NetBox detail-action path, if any.

        A detail-action path has exactly five non-empty segments —
        ``api / app / resource / id / action`` (e.g.
        ``/api/ipam/prefixes/5/available-ips/``) — with a numeric ``id`` in
        the fourth position. Anything else (a plain collection or detail
        path) returns ``None``.
        """
        parts = [part for part in path.split("/") if part]
        if len(parts) != 5 or parts[0] != "api" or not parts[3].isdigit():
            return None
        return parts[4]

    def _related_cache_paths(
        self, path: str, payload: dict[str, Any] | list[Any] | None
    ) -> list[str]:
        """Compute every cache path a successful write to ``path`` may have staled.

        A response cached before a write (e.g. the read-before-write step of
        an agent's documented operating sequence) must never be served again
        as if it reflected the write. This covers the exact path, its
        containing collection path (list/filter reads), each affected
        object's own detail path for bulk writes whose payload is a list of
        objects carrying an ``id`` (since bulk operations target the
        collection path rather than individual detail paths), and — for a
        recognized "detail action" endpoint such as ``available-ips`` — the
        unrelated collection(s) that action actually creates objects in.
        """
        paths = [path]
        collection_path = self._collection_path_for(path)
        if collection_path is not None and collection_path != path:
            paths.append(collection_path)
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "id" in item:
                    paths.append(f"{path.rstrip('/')}/{item['id']}/")
        action_name = self._trailing_action_name(path)
        if action_name is not None:
            paths.extend(_ACTION_CROSS_RESOURCE_CACHE_PATHS.get(action_name, ()))
        return paths

    def _invalidate_related_cache(
        self, path: str, payload: dict[str, Any] | list[Any] | None
    ) -> None:
        """Purge cached reads that a successful write to ``path`` may have staled.

        Each affected path is purged independently: a failure purging one
        path (e.g. a cache index lock timeout) must not prevent the remaining
        paths from being attempted. Skipping the rest after one early failure
        would leave paths such as the collection listing fully cached and
        able to serve a fresh-looking pre-write hit immediately after the
        write succeeds.
        """
        for target_path in self._related_cache_paths(path, payload):
            try:
                self._cache.invalidate_path(target_path)
            except OSError:
                logger.warning(
                    "cache invalidation failed after write attempt; stale reads "
                    "may be served until the affected entries expire",
                    extra={
                        "nbx_event": "http_cache_invalidate_failed",
                        "request_path": target_path,
                    },
                )

    def _safe_invalidate_related_cache(
        self, path: str, payload: dict[str, Any] | list[Any] | None
    ) -> None:
        """Best-effort cache purge that never overrides the underlying request outcome.

        Called both after a confirmed 2xx write and after an ambiguous
        request exception, since the write may have committed server-side
        either way. A cache-maintenance failure (e.g. an index file write
        error) must never propagate in its place — that would either
        misreport a successful write as failed, or mask the real request
        exception behind an unrelated filesystem error. `_invalidate_related_cache`
        already isolates per-path failures; this outer guard is a last-resort
        safety net for anything that still escapes it.
        """
        try:
            self._invalidate_related_cache(path, payload)
        except OSError:
            logger.warning(
                "cache invalidation failed after write attempt; stale reads "
                "may be served until the affected entries expire",
                extra={"nbx_event": "http_cache_invalidate_failed", "request_path": path},
            )

    def _cached_response(self, entry: CacheEntry, *, cache_status: str) -> ApiResponse:
        status, text, headers = entry.response_parts(cache_status=cache_status)
        return ApiResponse(status=status, text=text, headers=headers)

    def _finalize_cached_response(
        self,
        *,
        response: ApiResponse,
        cache_key: str | None,
        cache_entry: CacheEntry | None,
        cache_policy: CachePolicy | None,
        path: str,
        cache_generation: int | None = None,
    ) -> ApiResponse:
        if cache_policy is None or cache_key is None:
            return response
        if response.status == 304 and cache_entry is not None:
            refreshed = self._cache.refresh(
                cache_key,
                cache_entry,
                cache_policy,
                path=path,
                expected_generation=cache_generation,
            )
            return self._cached_response(refreshed, cache_status="REVALIDATED")
        if 200 <= response.status < 300:
            stored = self._cache.save(
                cache_key,
                response,
                cache_policy,
                path=path,
                expected_generation=cache_generation,
            )
            return self._cached_response(stored, cache_status="MISS")
        if (
            cache_entry is not None
            and cache_entry.can_serve_stale(self._now())
            and response.status >= 500
        ):
            return self._cached_response(cache_entry, cache_status="STALE")
        return response

    def _now(self) -> float:
        return time.time()

    async def probe_connection(self) -> ConnectionProbe:
        headers = {"Content-Type": "application/json"}
        try:
            response = await self.request("GET", "/", headers=headers)
        except Exception as exc:  # noqa: BLE001
            logger.warning("connection probe failed: %s", exc)
            return ConnectionProbe(status=0, version="", ok=False, error=str(exc))

        version = response.headers.get("API-Version", "")
        if response.status < 400 or response.status == 403:
            return ConnectionProbe(status=response.status, version=version, ok=True)

        return ConnectionProbe(
            status=response.status,
            version=version,
            ok=False,
            error=response.text[:500] if response.text else None,
        )

    async def get_version(self) -> str:
        """Gets the API version of NetBox via GET base URL and API-Version response header."""
        probe = await self.probe_connection()
        if probe.ok:
            return probe.version
        raise RequestError(ApiResponse(status=probe.status, text=probe.error or "", headers={}))

    async def status(self) -> dict[str, JSONValue]:
        response = await self.request("GET", "/api/status/")
        payload = response.json()
        if not isinstance(payload, dict):
            raise RequestError(response)
        return payload

    async def openapi(self) -> dict[str, JSONValue]:
        if self._openapi_cache is not None:
            return self._openapi_cache
        version = await self.get_version()
        path = "/api/schema/"
        try:
            major, minor = (int(part) for part in version.split(".")[:2])
        except (TypeError, ValueError):
            logger.debug(
                "could not parse netbox api version %r; assuming schema path /api/schema/",
                version,
            )
            major, minor = 999, 0
        if (major, minor) < (3, 5):
            path = "/api/docs/"
        query = None if path == "/api/schema/" else {"format": "openapi"}
        response = await self.request("GET", path, query=query)
        payload = response.json()
        if not isinstance(payload, dict):
            raise RequestError(response)
        self._openapi_cache = payload
        return self._openapi_cache

    async def create_token(self, username: str, password: str) -> ApiResponse:
        response = await self.request(
            "POST",
            "/api/users/tokens/provision/",
            payload={"username": username, "password": password},
        )
        if 200 <= response.status < 300:
            try:
                body = response.json()
            except json.JSONDecodeError:
                logger.debug(
                    "create_token success body is not json; returning raw response",
                    extra={"nbx_event": "create_token_non_json", "status": response.status},
                )
                return response
            if isinstance(body, dict):
                token_value = body.get("key")
                if isinstance(token_value, str) and token_value:
                    if token_value.startswith("nbt_") and "." in token_value:
                        token_key, token_secret = token_value.split(".", 1)
                        self.config.token_version = "v2"
                        self.config.token_key = token_key
                        self.config.token_secret = token_secret
                    else:
                        self.config.token_version = "v1"
                        self.config.token_key = None
                        self.config.token_secret = token_value
        return response

    @contextmanager
    def header_scope(self, **headers: str) -> Iterator[NetBoxApiClient]:
        """Apply additional request headers to all requests inside the with-block.

        Header scoping is per-task: the ContextVar copy taken when an asyncio
        Task is created means concurrent tasks (e.g. asyncio.gather) each see
        their own header set without races on shared state.
        """
        merged = dict(_scoped_headers.get() or {})
        merged.update({k: v for k, v in headers.items() if v})
        token = _scoped_headers.set(merged)
        try:
            yield self
        finally:
            _scoped_headers.reset(token)

    async def graphql(self, query: str, variables: dict[str, Any] | None = None) -> ApiResponse:
        """Execute a GraphQL query against the NetBox API."""
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        return await self.request("POST", "/api/graphql/", payload=payload)
