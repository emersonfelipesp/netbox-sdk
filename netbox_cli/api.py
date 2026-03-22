from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin, urlsplit

from pydantic import BaseModel, ConfigDict

from .config import Config, authorization_header_value, cache_dir
from .http_cache import CachePolicy, HttpCacheStore, build_cache_key


class ApiResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: int
    text: str
    headers: dict[str, str] = {}

    def json(self) -> Any:
        return json.loads(self.text)


class RequestError(RuntimeError):
    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Request failed with status {response.status}")


class ConnectionProbe(BaseModel):
    status: int
    version: str
    ok: bool
    error: str | None = None


class NetBoxApiClient:
    def __init__(self, config: Config):
        self.config = config
        self._cache = HttpCacheStore(cache_dir())

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
        query: dict[str, str] | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ApiResponse:
        try:
            import aiohttp
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "aiohttp is required for HTTP requests. Install project dependencies first."
            ) from exc

        authorization = authorization_header_value(self.config)
        cache_policy = self._cache_policy(
            method=method,
            path=path,
            query=query,
            payload=payload,
        )
        cache_key: str | None = None
        cache_entry = None
        req_headers = dict(headers or {})
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

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                response = await self._request_once(
                    session,
                    method=method,
                    path=path,
                    query=query,
                    payload=payload,
                    headers=req_headers,
                    authorization=authorization,
                )
            except Exception:
                if cache_entry is not None and cache_entry.can_serve_stale(self._now()):
                    return self._cached_response(cache_entry, cache_status="STALE")
                raise
            if self._should_retry_with_v1(response):
                response = await self._request_once(
                    session,
                    method=method,
                    path=path,
                    query=query,
                    payload=payload,
                    headers=req_headers,
                    authorization=self._v1_fallback_header(),
                )
            return self._finalize_cached_response(
                response=response,
                cache_key=cache_key,
                cache_entry=cache_entry,
                cache_policy=cache_policy,
            )

    async def _request_once(
        self,
        session: Any,
        *,
        method: str,
        path: str,
        query: dict[str, str] | None,
        payload: dict[str, Any] | list[Any] | None,
        headers: dict[str, str] | None,
        authorization: str | None,
    ) -> ApiResponse:
        req_headers = dict(headers or {})
        req_headers.setdefault("Accept", "application/json")
        if authorization:
            req_headers["Authorization"] = authorization

        async with session.request(
            method=method.upper(),
            url=self.build_url(path),
            params=query,
            json=payload,
            headers=req_headers,
        ) as response:
            text = await response.text()
            return ApiResponse(status=response.status, text=text, headers=dict(response.headers))

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

    def _cache_policy(
        self,
        *,
        method: str,
        path: str,
        query: dict[str, str] | None,
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

    def _cached_response(self, entry: Any, *, cache_status: str) -> ApiResponse:
        status, text, headers = entry.response_parts(cache_status=cache_status)
        return ApiResponse(status=status, text=text, headers=headers)

    def _finalize_cached_response(
        self,
        *,
        response: ApiResponse,
        cache_key: str | None,
        cache_entry: Any,
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
        import time

        return time.time()

    async def probe_connection(self) -> ConnectionProbe:
        headers = {"Content-Type": "application/json"}
        try:
            response = await self.request("GET", "/", headers=headers)
        except Exception as exc:  # noqa: BLE001
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
