from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from .config import Config, resolved_token


@dataclass(slots=True)
class ApiResponse:
    status: int
    text: str

    def json(self) -> Any:
        return json.loads(self.text)


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
                return ApiResponse(status=response.status, text=text)
