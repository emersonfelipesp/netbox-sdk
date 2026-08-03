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
        self,
        key: str,
        response: ApiResponse,
        policy: CachePolicy,
        *,
        path: str | None = None,
        expected_generation: int | None = None,
    ) -> CacheEntry:
        """Persist ``response`` as a cache entry, optionally fenced by ``expected_generation``.

        A GET that started before a concurrent write must never repopulate the
        cache after that write's ``invalidate_path`` has already run — doing so
        would resurrect stale data for the fresh TTL and stale-if-error window,
        hiding the mutation from subsequent reads. When ``path`` and
        ``expected_generation`` are both given, the entry write and index
        registration happen atomically under the same per-path lock
        ``invalidate_path`` uses, and are skipped entirely (the in-memory
        entry is still returned to satisfy the caller's own in-flight request)
        if the path's generation has advanced since ``expected_generation`` was
        captured.
        """
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
        if not path:
            self._write_entry(self._entry_path(key), entry)
            return entry
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            generation, keys = self._load_index_state(index_path)
            if expected_generation is not None and generation != expected_generation:
                return entry
            self._write_entry(self._entry_path(key), entry)
            if key not in keys:
                keys.append(key)
            self._write_index_state(index_path, generation, keys)
        return entry

    def path_generation(self, path: str) -> int:
        """Current invalidation generation for ``path``, to capture before a cacheable GET.

        Pass the returned value back to :meth:`save` as ``expected_generation``
        so a response that raced a concurrent write can detect the invalidation
        and skip persisting itself.
        """
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            generation, _keys = self._load_index_state(index_path)
            return generation

    def refresh(
        self,
        key: str,
        entry: CacheEntry,
        policy: CachePolicy,
        *,
        path: str | None = None,
        expected_generation: int | None = None,
    ) -> CacheEntry:
        """Extend TTLs for a 304-revalidated entry, optionally fenced by ``expected_generation``.

        Mirrors :meth:`save`'s fencing: a conditional GET that NetBox
        answered with 304 only confirms the representation matched the
        ETag/Last-Modified captured *before* the request, which a concurrent
        write's :meth:`invalidate_path` may have since invalidated. When
        ``path`` and ``expected_generation`` are both given, the refreshed
        entry is persisted only if the path's generation is unchanged;
        otherwise the already-purged on-disk entry is left untouched so the
        next read is a genuine cache miss instead of resurrecting pre-write
        data.
        """
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
        if not path:
            self._write_entry(self._entry_path(key), refreshed)
            return refreshed
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            generation, keys = self._load_index_state(index_path)
            if expected_generation is not None and generation != expected_generation:
                return refreshed
            self._write_entry(self._entry_path(key), refreshed)
            if key not in keys:
                keys.append(key)
            self._write_index_state(index_path, generation, keys)
        return refreshed

    def invalidate_path(self, path: str) -> None:
        """Purge every cached entry ever saved for the literal request ``path``.

        Entries are indexed by raw path (not the full cache key), so this
        removes every cached response for ``path`` regardless of which query
        string, scope headers, or bearer token produced it. Callers that know
        a mutation may have changed a resource must invalidate both the exact
        path and, where applicable, its containing collection path.

        The index file is rewritten with an incremented generation rather than
        deleted: a GET already in flight when this runs captured the
        pre-invalidation generation via :meth:`path_generation`, and its
        eventual :meth:`save` call must see a mismatch to know to discard
        itself instead of resurrecting the just-invalidated data. Deleting the
        index file outright would reset a fresh index back to generation 0,
        indistinguishable from one that was never invalidated.
        """
        index_path = self._index_path_file(path)
        with self._locked_index(index_path):
            generation, keys = self._load_index_state(index_path)
            for key in keys:
                self._entry_path(key).unlink(missing_ok=True)
            self._write_index_state(index_path, generation + 1, [])

    def _entry_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _index_path_file(self, path: str) -> Path:
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()
        return self.root / f"idx-{digest}.json"

    @contextlib.contextmanager
    def _locked_index(self, index_path: Path) -> Iterator[None]:
        """Serialize read-modify-write access to ``index_path`` across processes.

        ``save``, ``refresh``, and ``invalidate_path`` all do a
        load-then-replace cycle on the same per-path index file. Without a
        lock, two concurrent saves (e.g. the same path read under two
        different tokens or branches) can each load the same old index and
        overwrite it with only their own key, silently dropping the other
        key from the index — a later write's ``invalidate_path`` would then
        never purge the dropped entry, leaving it servable as a stale hit.
        This would also reopen the generation-fencing race the index is
        used for, since a fence check and its write must be atomic.

        On platforms without ``fcntl`` (e.g. Windows), a portable
        exclusive-create spin lock is used instead of the ``fcntl`` flock —
        never a no-op, which previously left both hazards above fully
        exposed on those platforms.
        """
        lock_path = index_path.with_name(index_path.name + ".lock")
        if fcntl is None:  # pragma: no cover - exercised via a forced monkeypatch in tests
            with self._portable_lock(lock_path):
                yield
            return
        lock_handle = lock_path.open("a+")
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()

    @contextlib.contextmanager
    def _portable_lock(
        self, lock_path: Path, *, timeout: float = 30.0, poll_interval: float = 0.01
    ) -> Iterator[None]:
        """Cross-platform exclusive lock via atomic file creation.

        ``O_CREAT | O_EXCL`` atomic exclusive-create is guaranteed by every
        supported filesystem, unlike ``fcntl.flock``. Unlike ``flock``, the
        lock file is not released automatically if the holding process dies,
        so a bounded ``timeout`` raises rather than deadlocking forever —
        strictly safer than the previous no-op, which corrupted the index
        silently instead of failing loudly.
        """
        deadline = time.monotonic() + timeout
        while True:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"timed out waiting for cache index lock: {lock_path}")
                time.sleep(poll_interval)
                continue
            os.close(fd)
            break
        try:
            yield
        finally:
            lock_path.unlink(missing_ok=True)

    def _load_index_state(self, index_path: Path) -> tuple[int, list[str]]:
        """Load ``(generation, keys)`` for a per-path index file.

        Missing, unreadable, or pre-generation-fencing files (a bare JSON
        list from an older cache layout) all resolve to a fresh
        ``(0, [])`` state — safe because a wrong generation only costs a
        few extra cache misses, never a stale hit.
        """
        if not index_path.exists():
            return 0, []
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0, []
        if isinstance(data, dict):
            generation = data.get("generation")
            keys = data.get("keys")
            if isinstance(generation, int) and isinstance(keys, list):
                return generation, [str(item) for item in keys]
        return 0, []

    def _write_index_state(self, index_path: Path, generation: int, keys: list[str]) -> None:
        payload = json.dumps({"generation": generation, "keys": keys})
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
