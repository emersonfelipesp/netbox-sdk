from __future__ import annotations

import hashlib
import json
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlencode

DEFAULT_FRESH_TTL_SECONDS = 60.0
DEFAULT_STALE_IF_ERROR_SECONDS = 300.0


@dataclass(slots=True)
class CachePolicy:
    fresh_ttl_seconds: float = DEFAULT_FRESH_TTL_SECONDS
    stale_if_error_seconds: float = DEFAULT_STALE_IF_ERROR_SECONDS


@dataclass(slots=True)
class CacheEntry:
    status: int
    text: str
    headers: dict[str, str]
    created_at: float
    fresh_until: float
    stale_if_error_until: float
    etag: str | None = None
    last_modified: str | None = None

    def is_fresh(self, now: float) -> bool:
        return now < self.fresh_until

    def can_serve_stale(self, now: float) -> bool:
        return now < self.stale_if_error_until

    def response_parts(self, *, cache_status: str) -> tuple[int, str, dict[str, str]]:
        headers = dict(self.headers)
        headers["X-NBX-Cache"] = cache_status
        return self.status, self.text, headers


def build_cache_key(
    *,
    base_url: str,
    method: str,
    path: str,
    query: dict[str, str] | None,
    authorization: str | None,
) -> str:
    encoded_query = urlencode(sorted((query or {}).items()), doseq=True)
    token_fingerprint = hashlib.sha256(
        (authorization or "").encode("utf-8")
    ).hexdigest()
    identity = "\n".join(
        [
            base_url.rstrip("/"),
            method.upper(),
            path,
            encoded_query,
            token_fingerprint,
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


class HttpCacheStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, key: str) -> CacheEntry | None:
        path = self._entry_path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        try:
            headers = payload.get("headers") or {}
            return CacheEntry(
                status=int(payload["status"]),
                text=str(payload["text"]),
                headers=dict(headers) if isinstance(headers, dict) else {},
                created_at=float(payload["created_at"]),
                fresh_until=float(payload["fresh_until"]),
                stale_if_error_until=float(payload["stale_if_error_until"]),
                etag=str(payload["etag"]) if payload.get("etag") else None,
                last_modified=(
                    str(payload["last_modified"])
                    if payload.get("last_modified")
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def save(self, key: str, response: ApiResponse, policy: CachePolicy) -> CacheEntry:
        now = time.time()
        headers = dict(response.headers)
        entry = CacheEntry(
            status=response.status,
            text=response.text,
            headers=headers,
            created_at=now,
            fresh_until=now + policy.fresh_ttl_seconds,
            stale_if_error_until=now + policy.stale_if_error_seconds,
            etag=headers.get("ETag"),
            last_modified=headers.get("Last-Modified"),
        )
        self._write_entry(self._entry_path(key), entry)
        return entry

    def refresh(self, key: str, entry: CacheEntry, policy: CachePolicy) -> CacheEntry:
        now = time.time()
        refreshed = CacheEntry(
            status=entry.status,
            text=entry.text,
            headers=dict(entry.headers),
            created_at=now,
            fresh_until=now + policy.fresh_ttl_seconds,
            stale_if_error_until=now + policy.stale_if_error_seconds,
            etag=entry.etag,
            last_modified=entry.last_modified,
        )
        self._write_entry(self._entry_path(key), refreshed)
        return refreshed

    def _entry_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _write_entry(self, path: Path, entry: CacheEntry) -> None:
        payload = json.dumps(asdict(entry), ensure_ascii=True, separators=(",", ":"))
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        temp_path.replace(path)
