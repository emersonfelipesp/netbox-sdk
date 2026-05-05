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
import time
from collections.abc import Callable, Iterator
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

if TYPE_CHECKING:
    import aiohttp

logger = logging.getLogger(__name__)

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
        normalized = parsed.path if parsed.path.startswith("/") else f"/{parsed.path}"
        return normalized

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
        req_headers = dict(_scoped_headers.get() or {})
        req_headers.update(headers or {})
        if cache_policy is not None and self.config.base_url:
            cache_key = build_cache_key(
                base_url=self.config.base_url,
                method=method,
                path=path,
                query=query,
                authorization=authorization,
            )
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
        try:
            response = await self._request_once(session, authorization=authorization, **req_kwargs)
        except Exception:
            logger.exception(
                "api request failed",
                extra={"http_method": method.upper(), "request_path": path},
            )
            if cache_entry is not None and cache_entry.can_serve_stale(self._now()):
                return self._cached_response(cache_entry, cache_status="STALE")
            raise
        if self._should_retry_with_v1(response):
            response = await self._request_once(
                session, authorization=self._v1_fallback_header(), **req_kwargs
            )
        elif self._should_refresh_demo_v1_token(response):
            authorization = self._refresh_demo_v1_authorization()
            if authorization:
                response = await self._request_once(
                    session, authorization=authorization, **req_kwargs
                )
        logger.info(
            "api request completed",
            extra={
                "http_method": method.upper(),
                "request_path": path,
                "status": response.status,
            },
        )
        return self._finalize_cached_response(
            response=response,
            cache_key=cache_key,
            cache_entry=cache_entry,
            cache_policy=cache_policy,
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
    ) -> ApiResponse:
        if cache_policy is None or cache_key is None:
            return response
        if response.status == 304 and cache_entry is not None:
            refreshed = self._cache.refresh(cache_key, cache_entry, cache_policy)
            return self._cached_response(refreshed, cache_status="REVALIDATED")
        if 200 <= response.status < 300:
            stored = self._cache.save(cache_key, response, cache_policy)
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
