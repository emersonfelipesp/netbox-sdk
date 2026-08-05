"""Filesystem-backed HTTP cache models and storage utilities for API responses."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import logging
import os
import secrets
import stat
import sys
import tempfile
import threading
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

# Real generations start at 0 and only ever increase, so this sentinel can
# never collide with one. Returned by path_generation() when the per-path
# lock could not be acquired, so callers treat "fencing was unavailable" the
# same as "the generation moved on" (skip persisting) instead of the lock
# outage blocking the request that fence exists to protect.
_LOCK_UNAVAILABLE_GENERATION = -1


def _pid_is_alive(pid: int) -> bool:
    """Best-effort check for whether ``pid`` still names a running process.

    Used only to decide whether a portable lock file (see ``_portable_lock``)
    was left behind by a process that has since died, versus one still
    legitimately holding it. Errors this function cannot interpret are
    treated as "alive" so a lock is never reclaimed out from under a holder
    this check simply failed to observe correctly.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":  # pragma: no cover - exercised only on Windows
        import ctypes

        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(  # type: ignore[attr-defined]
            process_query_limited_information, False, pid
        )
        if not handle:
            return False
        ctypes.windll.kernel32.CloseHandle(handle)  # type: ignore[attr-defined]
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


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
        self._unavailable_paths: set[str] = set()
        self._unavailable_paths_lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)
        self._set_private_permissions(self.root, stat.S_IRWXU)
        logger.debug(
            "http cache store ready",
            extra={"nbx_event": "http_cache_init", "cache_root": str(self.root)},
        )

    def load(self, key: str, *, path: str | None = None) -> CacheEntry | None:
        """Load ``key`` unless ``path`` is currently in durable bypass state."""
        if path is not None and self._path_is_unavailable(path):
            return None
        entry_path = self._entry_path(key)
        if not entry_path.exists():
            return None
        try:
            return CacheEntry.model_validate_json(entry_path.read_text(encoding="utf-8"))
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
        registration happen under the same per-path lock ``invalidate_path``
        uses, and are skipped entirely (the in-memory entry is still returned
        to satisfy the caller's own in-flight request) if the path's
        generation has advanced since ``expected_generation`` was captured.

        The index is registered *before* the entry file is written. Each
        individual write is already atomic (temp file + rename), but the pair
        together is not a single transaction — a crash or ``OSError`` between
        them must never leave an entry file that is invisible to
        ``invalidate_path`` (which only walks keys already registered in the
        index) yet still servable by ``load`` (which only checks that the
        entry file exists, never index membership). Registering the index
        first means the only possible interruption leaves an index key with
        no matching entry file, which ``load`` already treats as a safe
        cache miss.
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
        if expected_generation == _LOCK_UNAVAILABLE_GENERATION:
            # path_generation() already found the lock unavailable and
            # returned this sentinel; retrying the same lock here would only
            # repeat that outage for no benefit, since the mismatch below
            # would discard the write anyway.
            return entry
        if self._path_is_unavailable(path):
            return entry
        index_path = self._index_path_file(path)
        try:
            with self._locked_index(index_path):
                generation, keys, purged = self._load_index_state_or_purge(index_path, path)
                if purged:
                    logger.warning(
                        "netbox_sdk cache index for %s was corrupted and has been reset; "
                        "response was not cached",
                        path,
                        extra={"nbx_event": "cache_index_corrupted", "request_path": path},
                    )
                    return entry
                if expected_generation is not None and generation != expected_generation:
                    return entry
                if key not in keys:
                    keys.append(key)
                with self._locked_index(self._global_guard_path()):
                    if self._path_is_unavailable(path):
                        return entry
                    self._write_index_state(index_path, generation, keys)
                    self._write_entry(self._entry_path(key), entry)
        except TimeoutError:
            # A response was already received; failing to persist it to the
            # cache must never turn a successful request into a raised
            # exception. Log and return the in-memory entry unpersisted.
            logger.warning(
                "netbox_sdk cache index lock unavailable while saving %s; response was not cached",
                path,
                extra={"nbx_event": "cache_lock_timeout", "request_path": path},
            )
        return entry

    def path_generation(self, path: str) -> int:
        """Current invalidation generation for ``path``, to capture before a cacheable GET.

        Pass the returned value back to :meth:`save` as ``expected_generation``
        so a response that raced a concurrent write can detect the invalidation
        and skip persisting itself.

        If the per-path lock cannot be acquired — a stale lock predating
        PID-based reclamation, or genuine contention outliving the timeout —
        this degrades to :data:`_LOCK_UNAVAILABLE_GENERATION` rather than
        propagating the failure. A lock outage must never block the GET this
        fence exists to protect from ever reaching NetBox.
        """
        if self._path_is_unavailable(path):
            try:
                # A previous invalidation timed out after a mutation may have
                # committed. Complete that purge before trusting any entry
                # that survived the failed attempt. invalidate_path() clears
                # only the unavailable markers that predated this successful
                # purge, so a newer concurrent timeout cannot be lost.
                self.invalidate_path(path)
            except OSError:
                logger.warning(
                    "netbox_sdk cache index lock unavailable for %s; skipping cache for this request",
                    path,
                    extra={"nbx_event": "cache_lock_timeout", "request_path": path},
                )
                return _LOCK_UNAVAILABLE_GENERATION

        index_path = self._index_path_file(path)
        try:
            with self._locked_index(index_path):
                generation, _keys, purged = self._load_index_state_or_purge(index_path, path)
                if purged:
                    logger.warning(
                        "netbox_sdk cache index for %s was corrupted and has been reset; "
                        "skipping cache for this request",
                        path,
                        extra={"nbx_event": "cache_index_corrupted", "request_path": path},
                    )
                    return _LOCK_UNAVAILABLE_GENERATION
                return generation
        except TimeoutError:
            self._mark_path_unavailable(path)
            logger.warning(
                "netbox_sdk cache index lock unavailable for %s; skipping cache for this request",
                path,
                extra={"nbx_event": "cache_lock_timeout", "request_path": path},
            )
            return _LOCK_UNAVAILABLE_GENERATION

    @staticmethod
    def generation_is_available(generation: int) -> bool:
        """Return whether ``generation`` was captured under cache coordination."""
        return generation != _LOCK_UNAVAILABLE_GENERATION

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

        As in :meth:`save`, the index is registered before the entry file is
        written so an interrupted commit degrades to a safe cache miss
        instead of an entry that ``invalidate_path`` can never discover.
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
        if expected_generation == _LOCK_UNAVAILABLE_GENERATION:
            return refreshed
        if self._path_is_unavailable(path):
            return refreshed
        index_path = self._index_path_file(path)
        try:
            with self._locked_index(index_path):
                generation, keys, purged = self._load_index_state_or_purge(index_path, path)
                if purged:
                    logger.warning(
                        "netbox_sdk cache index for %s was corrupted and has been reset; "
                        "entry was not persisted",
                        path,
                        extra={"nbx_event": "cache_index_corrupted", "request_path": path},
                    )
                    return refreshed
                if expected_generation is not None and generation != expected_generation:
                    return refreshed
                if key not in keys:
                    keys.append(key)
                with self._locked_index(self._global_guard_path()):
                    if self._path_is_unavailable(path):
                        return refreshed
                    self._write_index_state(index_path, generation, keys)
                    self._write_entry(self._entry_path(key), refreshed)
        except TimeoutError:
            logger.warning(
                "netbox_sdk cache index lock unavailable while refreshing %s; entry was not persisted",
                path,
                extra={"nbx_event": "cache_lock_timeout", "request_path": path},
            )
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
        unavailable_markers = self._path_unavailable_markers(path)
        index_path = self._index_path_file(path)
        try:
            with self._locked_index(index_path):
                # A `purged` result here is not special-cased: invalidate_path
                # already writes a fresh, incremented generation below
                # regardless, and the corruption-triggered unavailable marker
                # _load_index_state_or_purge just set predates the
                # `unavailable_markers` snapshot above, so it correctly
                # survives this call's own _clear_path_unavailable and
                # self-heals on the next path_generation() call for path.
                generation, keys, _purged = self._load_index_state_or_purge(index_path, path)
                with self._locked_index(self._global_guard_path()):
                    for key in keys:
                        self._entry_path(key).unlink(missing_ok=True)
                    self._write_index_state(index_path, generation + 1, [])
        except TimeoutError:
            # The mutation may already be committed, while the pre-write
            # entry is still present. Make that uncertainty visible to every
            # cache-store instance sharing this root so reads bypass the
            # entry until a later path_generation() can complete the purge.
            self._mark_path_unavailable(path)
            raise
        self._clear_path_unavailable(path, unavailable_markers)

    def _unavailable_marker_prefix(self, path: str) -> str:
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()
        return self._unavailable_marker_prefix_for_digest(digest)

    @staticmethod
    def _unavailable_marker_prefix_for_digest(digest: str) -> str:
        return f"unavailable-{digest}-"

    def _path_unavailable_markers(self, path: str) -> tuple[Path, ...]:
        prefix = self._unavailable_marker_prefix(path)
        return tuple(self.root.glob(f"{prefix}*.marker"))

    def _path_is_unavailable(self, path: str) -> bool:
        with self._unavailable_paths_lock:
            return path in self._unavailable_paths or bool(self._path_unavailable_markers(path))

    def _mark_path_unavailable(self, path: str) -> None:
        """Force cache reads for ``path`` to bypass entries after a lock timeout.

        Each timeout gets a unique marker. A successful invalidation removes
        only markers it observed before taking the path lock; if another
        invalidation times out concurrently, its newer marker survives and
        keeps the path unavailable until that uncertainty is purged too.
        """
        with self._unavailable_paths_lock:
            self._unavailable_paths.add(path)
            if not self._write_unavailable_marker(self._unavailable_marker_prefix(path)):
                # The process-local state still protects this client even if
                # the filesystem is too unhealthy to publish the marker to
                # other cache-store instances.
                logger.warning(
                    "netbox_sdk could not persist cache-unavailable marker for %s",
                    path,
                    extra={"nbx_event": "cache_marker_write_failed", "request_path": path},
                )

    def _mark_index_digest_unavailable(self, digest: str) -> bool:
        """Publish bypass state for an index whose plaintext path is unknown."""
        with self._unavailable_paths_lock:
            persisted = self._write_unavailable_marker(
                self._unavailable_marker_prefix_for_digest(digest)
            )
        if not persisted:
            logger.warning(
                "netbox_sdk could not persist cache-unavailable marker for index %s",
                digest[:16],
                extra={"nbx_event": "cache_marker_write_failed"},
            )
        return persisted

    def _write_unavailable_marker(self, prefix: str) -> bool:
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.root,
                prefix=prefix,
                suffix=".marker",
                delete=False,
            ) as handle:
                marker_path = Path(handle.name)
            self._set_private_permissions(marker_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            return False
        return True

    def _clear_path_unavailable(self, path: str, markers: tuple[Path, ...]) -> None:
        with self._unavailable_paths_lock:
            for marker_path in markers:
                try:
                    marker_path.unlink(missing_ok=True)
                except OSError:
                    # A marker that cannot be removed safely keeps this path
                    # in bypass mode; a later successful purge can retry it.
                    pass
            if not self._path_unavailable_markers(path):
                self._unavailable_paths.discard(path)

    def _global_guard_path(self) -> Path:
        """Nominal path whose neighboring ``.lock`` file serializes purges against writes.

        Never read or written itself — only passed to :meth:`_locked_index`
        so ``save``, ``refresh``, and ``invalidate_path`` can take out the
        same lock :meth:`_purge_all_entries` uses around its own deletion
        pass, via the same per-path locking primitive those methods already
        use for their own index file.
        """
        return self.root / "__global_purge_guard__"

    def _purge_all_entries(self, corrupted_index_path: Path) -> None:
        """Recover from ``corrupted_index_path`` without disturbing any healthy path.

        The fail-safe fallback used by :meth:`_load_index_state_or_purge`
        (and therefore by ``save``, ``refresh``, ``path_generation``, and
        ``invalidate_path`` alike) when a corrupted index makes it
        impossible to enumerate which entries it registered — its ``keys``
        list is gone, so the only entry files known to be safe to keep are
        the ones every *other*, still-parseable index file still lists.
        Deleting every ``*.json`` file store-wide unconditionally (an
        earlier version of this method) reset every other path's generation
        back to 0 too, which reopened the very race this fencing scheme
        exists to close: an in-flight GET for an unrelated, healthy path
        could capture generation 0, lose a race against that path's own
        concurrent write bumping it to 1, and then have this purge silently
        rewind it back to 0 — indistinguishable from the pre-write value the
        GET originally captured — letting its now-stale ``save`` pass the
        fence and resurrect data the write had already invalidated.

        Only ``corrupted_index_path`` itself is reset directly. Any *other*
        index file that independently fails to parse while this scan runs is
        replaced by a durable digest-keyed unavailable marker (or retained
        as a corrupted sentinel if publishing that marker fails); every
        entry file still listed by a healthy index, and that index's own
        generation, is left completely untouched, so no unrelated path's
        fencing can ever observe a rewound generation from this call. An
        entry file not listed by any surviving index — including every entry
        the corrupted index used to register — is deleted, since ``save``
        and ``refresh`` always register a key in its index *before* writing
        the entry file (see their docstrings), so under normal operation an
        entry is never left unlisted by every valid index; the only way one
        can be is if the index that used to list it is the corrupted one
        being recovered from here.

        The whole scan-and-delete pass runs under :meth:`_global_guard_path`'s
        lock, the same lock ``save``/``refresh``/``invalidate_path`` take out
        around their own index-then-entry write pair (never around their full
        critical section, which would self-deadlock against this very call —
        this method is only ever reached from inside one of those methods'
        *own* per-path lock, before that caller has acquired the guard
        itself). Without this, this pass could race a concurrent writer for a
        *different, healthy* path that had already written its per-path
        index (registering a new key) but not yet its entry file: the scan
        below would see that key already listed in a "healthy" index and
        correctly spare it, but only because the write is serialized to
        either fully precede or fully follow this call — interleaved, the
        entry file could still be missing when this pass looks for it,
        which is harmless (an absent file is simply not unlinked), while a
        *reversed* interleaving (entry visible, index not yet updated) is
        exactly what this lock rules out.
        """
        with self._locked_index(self._global_guard_path()):
            known_keys: set[str] = set()
            for index_path in self.root.glob("idx-*.json"):
                if index_path == corrupted_index_path:
                    continue
                state = self._load_index_state_or_none(index_path)
                if state is None:
                    # A second, independently corrupted index found while
                    # recovering from the first. Its keys are just as
                    # unrecoverable. Publish bypass state using the digest
                    # shared by its index name and unavailable-marker prefix
                    # before removing it; otherwise a later missing index
                    # would look like a trustworthy generation 0 and let a
                    # stale save/refresh rewind its invalidation fence. If
                    # marker persistence fails, retain the corrupted index
                    # itself as the fail-safe sentinel until its plaintext
                    # path is accessed and can mark process-local state too.
                    digest = index_path.name.removeprefix("idx-").removesuffix(".json")
                    if self._mark_index_digest_unavailable(digest):
                        index_path.unlink(missing_ok=True)
                    continue
                _generation, keys = state
                known_keys.update(keys)
            corrupted_index_path.unlink(missing_ok=True)
            for cached_file in self.root.glob("*.json"):
                if cached_file.name.startswith("idx-"):
                    continue
                if cached_file.stem not in known_keys:
                    cached_file.unlink(missing_ok=True)

    def _entry_path(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def _index_path_file(self, path: str) -> Path:
        digest = hashlib.sha256(path.encode("utf-8")).hexdigest()
        return self.root / f"idx-{digest}.json"

    @contextlib.contextmanager
    def _locked_index(
        self, index_path: Path, *, timeout: float = 30.0, poll_interval: float = 0.01
    ) -> Iterator[None]:
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

        ``timeout``/``poll_interval`` bound both branches identically.
        ``_acquire_flock`` polls non-blocking so both lock backends raise
        :class:`TimeoutError` on the same bounded deadline and every
        existing caller's timeout handling (cache bypass, unavailable-path
        marking) applies to both. ``NetBoxApiClient`` runs these synchronous
        cache operations in worker threads so the required wait-then-succeed
        behavior never stalls its asyncio event loop.
        """
        lock_path = index_path.with_name(index_path.name + ".lock")
        if fcntl is None:  # pragma: no cover - exercised via a forced monkeypatch in tests
            with self._portable_lock(lock_path, timeout=timeout, poll_interval=poll_interval):
                yield
            return
        lock_handle = lock_path.open("a+")
        try:
            self._acquire_flock(lock_handle, timeout=timeout, poll_interval=poll_interval)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()

    def _acquire_flock(
        self, lock_handle, *, timeout: float = 30.0, poll_interval: float = 0.01
    ) -> None:
        """Acquire an exclusive ``flock`` without ever blocking indefinitely.

        ``fcntl.flock(..., LOCK_EX)`` blocks until the lock is free with no
        way to bound the wait. Polling ``LOCK_EX | LOCK_NB`` on a deadline
        instead mirrors :meth:`_portable_lock`'s own bounded-timeout
        contract, so a lock held by another live, stopped, or wedged process
        surfaces as the same :class:`TimeoutError` every caller already
        handles instead of hanging the caller forever.

        Only ``EAGAIN``/``EACCES`` report lock contention for this
        nonblocking operation. Other ``OSError`` values are real lock or
        filesystem failures and are propagated immediately rather than
        hidden behind the contention timeout.
        """
        if fcntl is None:  # pragma: no cover - guarded by _locked_index's own check
            raise RuntimeError("_acquire_flock requires the fcntl module")
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"timed out waiting for cache index lock: {lock_handle.name}"
                    )
                time.sleep(poll_interval)

    @contextlib.contextmanager
    def _portable_lock(
        self, lock_path: Path, *, timeout: float = 30.0, poll_interval: float = 0.01
    ) -> Iterator[None]:
        """Cross-platform exclusive lock via atomic file creation.

        ``O_CREAT | O_EXCL`` atomic exclusive-create is guaranteed by every
        supported filesystem, unlike ``fcntl.flock``. Unlike ``flock``, the
        lock file is not released automatically if the holding process dies.
        The lock file records the creating process's PID so a waiter that
        finds the file already present can tell a genuinely held lock apart
        from one abandoned by a crashed process and reclaim the latter
        immediately instead of waiting out the full ``timeout`` — left
        unreclaimed, a crash here would poison every later cacheable request
        through this path forever, since nothing else ever removes the file.
        A lock file this check cannot attribute to a live or dead PID (e.g.
        one left by an older SDK version, or read mid-write) is left alone
        and only cleared by the bounded ``timeout`` below, which still raises
        rather than deadlocking forever.
        """
        deadline = time.monotonic() + timeout
        owner_record: str | None = None
        while owner_record is None:
            owner_record = self._try_create_portable_lock(lock_path)
            if owner_record is None:
                owner_record = self._reclaim_stale_lock(lock_path)
            if owner_record is not None:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out waiting for cache index lock: {lock_path}")
            time.sleep(poll_interval)
        try:
            yield
        finally:
            self._release_portable_lock(lock_path, owner_record)

    def _try_create_portable_lock(self, lock_path: Path) -> str | None:
        """Atomically create ``lock_path`` and return its unique owner record."""
        owner_record = f"{os.getpid()}:{secrets.token_hex(16)}"
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return None
        try:
            payload = owner_record.encode("ascii")
            offset = 0
            while offset < len(payload):
                written = os.write(fd, payload[offset:])
                if written <= 0:
                    raise OSError("failed to write cache lock owner record")
                offset += written
        except BaseException:
            os.close(fd)
            lock_path.unlink(missing_ok=True)
            raise
        os.close(fd)
        return owner_record

    def _read_portable_lock_record(self, lock_path: Path) -> tuple[int, str] | None:
        try:
            content = lock_path.read_text(encoding="ascii").strip()
            pid_text, separator, token = content.partition(":")
            if separator and not token:
                return None
            pid = int(pid_text)
        except (OSError, UnicodeDecodeError, ValueError):
            return None
        return pid, content

    def _release_portable_lock(self, lock_path: Path, owner_record: str) -> None:
        current = self._read_portable_lock_record(lock_path)
        if current is None or current[1] != owner_record:
            return
        lock_path.unlink(missing_ok=True)

    def _reclaim_stale_lock(self, lock_path: Path) -> str | None:
        """Atomically replace a dead owner's lock and return our owner record.

        Only a lock file whose contents are a plain PID written by
        an older SDK or a PID plus unique token written by this version is
        eligible. Reclaimers for the exact observed record serialize through
        an exclusive claim file, re-read the owner record while holding that
        claim, and create the replacement lock before releasing the claim.
        A second waiter therefore cannot unlink the first waiter's newly
        created live lock after both initially observed the same stale file.
        """
        observed = self._read_portable_lock_record(lock_path)
        if observed is None:
            return None
        pid, owner_record = observed
        if _pid_is_alive(pid):
            return None

        claim_digest = hashlib.sha256(owner_record.encode("ascii")).hexdigest()
        claim_path = lock_path.with_name(f"{lock_path.name}.reclaim-{claim_digest}")
        claim_record = self._try_create_portable_lock(claim_path)
        if claim_record is None:
            return None
        try:
            current = self._read_portable_lock_record(lock_path)
            if current is None or current[1] != owner_record:
                return None
            try:
                lock_path.unlink()
            except FileNotFoundError:
                return None
            # Keep the record-specific claim until after this exclusive
            # create. Ordinary contenders may win the unlink/create gap, but
            # then this returns None and waits; no second stale reclaimer can
            # remove whichever live replacement won.
            return self._try_create_portable_lock(lock_path)
        finally:
            self._release_portable_lock(claim_path, claim_record)

    def _load_index_state_or_none(self, index_path: Path) -> tuple[int, list[str]] | None:
        """Load ``(generation, keys)``, distinguishing "never written" from "corrupted".

        A missing file resolves to a safe ``(0, [])`` state, but a file that
        exists yet cannot be parsed as a valid index resolves to ``None``
        instead of silently discarding its (unrecoverable) ``keys`` list —
        callers must not treat "corrupted" the same as "empty", since doing
        so anywhere would let this path's stale entry files go on being
        served as fresh hits by ``load`` (which decides hits by entry-file
        existence alone, never index membership) forever. Use
        :meth:`_load_index_state_or_purge` rather than this method directly
        unless the caller has its own reason to handle ``None`` differently.
        """
        if not index_path.exists():
            return 0, []
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict):
            generation = data.get("generation")
            keys = data.get("keys")
            if isinstance(generation, int) and isinstance(keys, list):
                return generation, [str(item) for item in keys]
        return None

    def _load_index_state_or_purge(
        self, index_path: Path, path: str
    ) -> tuple[int, list[str], bool]:
        """Load ``(generation, keys, purged)``, recovering ``index_path`` on corruption.

        Shared by every method that reads a per-path index (``save``,
        ``refresh``, ``path_generation``, and ``invalidate_path``). A
        corrupted index's ``keys`` list is unrecoverable (see
        :meth:`_load_index_state_or_none`), so any of these four call sites
        finding one recovers via :meth:`_purge_all_entries` rather than
        silently degrading to an empty index. Degrading to empty instead —
        as an earlier version of this cache did in ``save`` and ``refresh``
        — let an ordinary write for a different key on the same corrupted
        path "heal" the on-disk index with a fresh, valid-looking one that
        permanently forgot every key the corrupted index still registered:
        those keys' entry files were never purged and never
        index-discoverable again, yet kept being served as fresh hits by
        ``load`` forever, even past the next ``invalidate_path`` call for
        that same path. :meth:`_purge_all_entries` only resets the entries
        this specific corrupted index could no longer account for — every
        other path's index and generation is left untouched, so this never
        costs an unrelated path anything beyond what its own writes already
        do.

        ``purged`` is ``True`` when this call reset ``index_path`` after
        finding it corrupted. The recovered generation is always ``0``, but
        it must never be trusted as a real fence value: a GET could have
        captured ``expected_generation=0`` on this same path *before* a
        concurrent write advanced it to 1, and if the index then turns out
        corrupted (for any unrelated reason) by the time that GET's
        ``save``/``refresh`` runs, the naive reset would make its stale
        ``expected_generation=0`` match the recovered ``0`` and persist the
        stale response, hiding the committed mutation. ``_mark_path_unavailable``
        is called here so every caller can treat a ``purged`` result exactly
        like a lock-timeout outage — skip the affected persist/fence — and so
        the next ``path_generation`` call self-heals it via the existing
        ``invalidate_path`` bypass-and-clear flow used for lock timeouts.
        """
        state = self._load_index_state_or_none(index_path)
        if state is None:
            self._purge_all_entries(index_path)
            self._mark_path_unavailable(path)
            return 0, [], True
        return state[0], state[1], False

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
