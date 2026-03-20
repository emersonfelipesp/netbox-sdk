from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from .config import Config, resolved_token


@dataclass(slots=True)
class ApiResponse:
    status: int
    text: str
    headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        return json.loads(self.text)


class RequestError(RuntimeError):
    def __init__(self, response: ApiResponse):
        self.response = response
        super().__init__(f"Request failed with status {response.status}")


@dataclass(slots=True)
class ConnectionProbe:
    status: int
    version: str
    ok: bool
    error: str | None = None


class NetBoxApiClient:
    def __init__(self, config: Config):
        self.config = config

    def build_url(self, path: str) -> str:
        if not self.config.base_url:
            raise RuntimeError("NetBox base URL is not configured")
        normalized = path if path.startswith("/") else f"/{path}"
        return urljoin(f"{self.config.base_url.rstrip('/')}/", normalized.lstrip("/"))

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
            raise RuntimeError("aiohttp is required for HTTP requests. Install project dependencies first.") from exc

        req_headers = dict(headers or {})
        req_headers.setdefault("Accept", "application/json")
        token = resolved_token(self.config)
        if token:
            req_headers.setdefault("Authorization", f"Bearer {token}")

        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method=method.upper(),
                url=self.build_url(path),
                params=query,
                json=payload,
                headers=req_headers,
            ) as response:
                text = await response.text()
                return ApiResponse(status=response.status, text=text, headers=dict(response.headers))

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
