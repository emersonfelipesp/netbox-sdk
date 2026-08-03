"""Filesystem-backed HTTP cache models and storage utilities for API responses."""

from __future__ import annotations

import contextlib
import hashlib
import json
import logging
import os
import stat
import tempfile
import time
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from pydantic import BaseModel, ValidationError

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms (e.g. Windows)
    fcntl = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from netbox_sdk.client import ApiResponse

logger = logging.getLogger(__name__)

QueryParamValue = str | list[str]
QueryParams = dict[str, QueryParamValue]

DEFAULT_FRESH_TTL_SECONDS = 60.0
DEFAULT_STALE_IF_ERROR_SECONDS = 300.0


class CachePolicy(BaseModel):
    """TTL policy for treating a cache entry as fresh and when stale entries may be served on error."""

    fresh_ttl_seconds: float = DEFAULT_FRESH_TTL_SECONDS
    stale_if_error_seconds: float = DEFAULT_STALE_IF_ERROR_SECONDS


class CacheEntry(BaseModel):
    """Serialized HTTP response plus metadata for cache lookup and conditional requests."""

    status: int
    text: str
    headers: dict[str, str]
    created_at: float
    fresh_until: float
    stale_if_error_until: float
    etag: str | None = None
    last_modified: str | None = None

    def is_fresh(self, now: float) -> bool:
        """True if ``now`` is before the fresh-until timestamp."""
        return now < self.fresh_until

    def can_serve_stale(self, now: float) -> bool:
        """True if a stale entry may still be returned after upstream errors."""
        return now < self.stale_if_error_until

    def response_parts(self, *, cache_status: str) -> tuple[int, str, dict[str, str]]:
        """Status, body, and headers including ``X-NBX-Cache`` for synthetic responses."""
        headers = dict(self.headers)
        headers["X-NBX-Cache"] = cache_status
        return self.status, self.text, headers


def build_cache_key(
    *,
    base_url: str,
    method: str,
    path: str,
    query: QueryParams | None,
    authorization: str | None,
    scope_headers: dict[str, str] | None = None,
) -> str:
    """Build a stable SHA-256 cache key from URL identity (no raw secrets in the key file name).

    ``scope_headers`` must include every request header that can change the
    server-side representation for an otherwise-identical method/path/query,
    such as ``X-NetBox-Branch``. Two requests that differ only by such a
    header (e.g. the same token reading two different NetBox Branching
    schemas) must never collide on the same cached entry.
    """
    encoded_query = urlencode(sorted((query or {}).items()), doseq=True)
    token_fingerprint = hashlib.sha256((authorization or "").encode("utf-8")).hexdigest()
    normalized_scope = sorted(
        (name.lower(), value)
        for name, value in (scope_headers or {}).items()
        if name.lower() != "authorization"
    )
    scope_fingerprint = hashlib.sha256(
        "\n".join(f"{name}:{value}" for name, value in normalized_scope).encode("utf-8")
    ).hexdigest()
    identity = "\n".join(
        [
            base_url.rstrip("/"),
            method.upper(),
            path,
            encoded_query,
            token_fingerprint,
            scope_fingerprint,
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


class HttpCacheStore:
    """Filesystem JSON store for cached :class:`CacheEntry` records under ``root``."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self._set_private_permissions(self.root, stat.S_IRWXU)
        logger.debug(
            "http cache store ready",
            extra={"nbx_event": "http_cache_init", "cache_root": str(self.root)},
        )

    def load(self, key: str) -> CacheEntry | None:
        path = self._entry_path(key)
        if not path.exists():
            return None
        try:
            return CacheEntry.model_validate_json(path.read_text(encoding="utf-8"))
        except OSError:
            logger.debug(
                "cache entry read failed",
                extra={"nbx_event": "http_cache_load_oserror", "cache_key_prefix": key[:16]},
            )
            return None
        except ValidationError as exc:
            logger.debug(
                "cache entry invalid, ignoring: %s",
                exc,
                extra={"nbx_event": "http_cache_load_invalid", "cache_key_prefix": key[:16]},
            )
            return None

    def save(
        self, key: str, response: ApiResponse, policy: CachePolicy, *, path: str | None = None
    ) -> CacheEntry:
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
        if path:
            self._record_path_index(path, key)
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

    def invalidate_path(self, path: str) -> None:
        """Purge every cached entry ever saved for the literal request ``path``.

        Entries are indexed by raw path (not the full cache key), so this
        removes every cached response for ``path`` regardless of which query
        string, scope headers, or bearer token produced it. Callers that know
        a mutation may have changed a resource must invalidate both the exact
        path and, where applicable, its containing collection path.
        """
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            keys = self._load_index(index_path)
            for key in keys:
                self._entry_path(key).unlink(missing_ok=True)
            index_path.unlink(missing_ok=True)

    def _entry_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _index_path_file(self, path: str) -> Path:
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()
        return self.root / f"idx-{digest}.json"

    @contextlib.contextmanager
    def _locked_index(self, index_path: Path) -> Iterator[None]:
        """Serialize read-modify-write access to ``index_path`` across processes.

        ``_record_path_index`` and ``invalidate_path`` both do a
        load-then-replace cycle on the same per-path index file. Without a
        lock, two concurrent saves (e.g. the same path read under two
        different tokens or branches) can each load the same old index and
        overwrite it with only their own key, silently dropping the other
        key from the index — a later write's ``invalidate_path`` would then
        never purge the dropped entry, leaving it servable as a stale hit.
        """
        if fcntl is None:  # pragma: no cover - non-POSIX platforms
            yield
            return
        lock_path = index_path.with_name(index_path.name + ".lock")
        lock_handle = lock_path.open("a+")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()

    def _record_path_index(self, path: str, key: str) -> None:
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            keys = self._load_index(index_path)
            if key not in keys:
                keys.append(key)
                self._write_index(index_path, keys)

    def _load_index(self, index_path: Path) -> list[str]:
        if not index_path.exists():
            return []
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        return [str(item) for item in data]

    def _write_index(self, index_path: Path, keys: list[str]) -> None:
        payload = json.dumps(keys)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=index_path.parent,
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        try:
            temp_path.replace(index_path)
        except OSError:
            temp_path.unlink(missing_ok=True)
            raise
        self._set_private_permissions(index_path, stat.S_IRUSR | stat.S_IWUSR)

    def _write_entry(self, path: Path, entry: CacheEntry) -> None:
        payload = entry.model_dump_json()
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_path = Path(handle.name)
        try:
            temp_path.replace(path)
        except OSError:
            temp_path.unlink(missing_ok=True)
            raise
        self._set_private_permissions(path, stat.S_IRUSR | stat.S_IWUSR)

    def _set_private_permissions(self, path: Path, mode: int) -> None:
        try:
            if os.name != "nt":
                path.chmod(mode)
        except OSError:
            return
