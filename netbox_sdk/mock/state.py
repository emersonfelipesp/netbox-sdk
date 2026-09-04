"""Thread-safe in-memory state store for the NetBox mock API."""

from __future__ import annotations

import hashlib
import os
import threading
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

_store_lock = threading.Lock()
_stores: dict[str, ThreadSafeMockStore] = {}


@dataclass(slots=True)
class _BackgroundJob:
    record: dict[str, Any]
    object_key: str
    collection_key: str
    operation: Callable[[], tuple[bool, Any]]
    pending_polls: int = 1


class ThreadSafeMockStore:
    """Thread-safe in-memory CRUD state store for the NetBox mock API.

    Uses a plain Python dict with a reentrant lock. Supports the same
    interface as the proxmox-sdk SharedMemoryMockStore for easy porting,
    but without shared memory or inter-process coordination.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._objects: dict[str, Any] = {}
        self._collections: dict[str, dict[str, Any]] = {}
        self._deleted: set[str] = set()
        self._id_counters: dict[str, int] = {}
        self._background_jobs: dict[int, _BackgroundJob] = {}
        self._schema_fingerprint: str = ""

    def touch_schema(self, fingerprint: str) -> bool:
        """Reset state if the schema fingerprint changed. Returns True if reset."""
        with self._lock:
            if self._schema_fingerprint == fingerprint:
                return False
            self._schema_fingerprint = fingerprint
            self._objects.clear()
            self._collections.clear()
            self._deleted.clear()
            self._id_counters.clear()
            self._background_jobs.clear()
            return True

    def reset(self) -> None:
        """Clear all stored objects, collections, and tombstones."""
        with self._lock:
            self._objects.clear()
            self._collections.clear()
            self._deleted.clear()
            self._id_counters.clear()
            self._background_jobs.clear()

    # --- Object store ---

    def get_object(self, key: str) -> Any | None:
        """Return a deep copy of a stored object, or None if not present."""
        with self._lock:
            value = self._objects.get(key)
            return deepcopy(value)

    def set_object(self, key: str, value: Any) -> Any:
        """Store an object and return the persisted copy."""
        with self._lock:
            self._objects[key] = deepcopy(value)
            self._deleted.discard(key)
            return deepcopy(value)

    def delete_object(self, key: str) -> None:
        """Delete an object and mark it as removed."""
        with self._lock:
            self._objects.pop(key, None)
            self._deleted.add(key)

    def is_deleted(self, key: str) -> bool:
        """Return True if the key has been explicitly deleted."""
        with self._lock:
            return key in self._deleted

    # --- Collection store ---

    def get_collection(self, key: str) -> list[Any] | None:
        """Return a list copy of a stored collection, or None if not initialized."""
        with self._lock:
            members = self._collections.get(key)
            if members is None:
                return None
            return [deepcopy(v) for v in members.values()]

    def replace_collection(self, key: str, values: list[Any]) -> list[Any]:
        """Replace an entire collection with the provided values list."""
        with self._lock:
            self._collections[key] = {f"seed:{i}": deepcopy(v) for i, v in enumerate(values)}
            return [deepcopy(v) for v in values]

    def upsert_collection_member(self, key: str, member_key: str, value: Any) -> list[Any]:
        """Insert or replace a member in a stored collection."""
        with self._lock:
            members = self._collections.setdefault(key, {})
            members[member_key] = deepcopy(value)
            self._deleted.discard(member_key)
            return [deepcopy(item) for item in members.values()]

    def delete_collection_member(self, key: str, member_key: str) -> list[Any]:
        """Remove a member from a stored collection."""
        with self._lock:
            members = self._collections.setdefault(key, {})
            members.pop(member_key, None)
            self._deleted.add(member_key)
            return [deepcopy(item) for item in members.values()]

    # --- NetBox-specific: auto-incrementing integer IDs ---

    def next_id(self, collection_path: str) -> int:
        """Atomically increment and return the next integer ID for a collection."""
        with self._lock:
            current = self._id_counters.get(collection_path, 0)
            next_val = current + 1
            self._id_counters[collection_path] = next_val
            return next_val

    def peek_next_id(self, collection_path: str) -> int:
        """Return what the next ID would be without incrementing."""
        with self._lock:
            return self._id_counters.get(collection_path, 0) + 1

    # --- Deterministic background jobs ---

    def queue_background_job(
        self,
        job_id: int,
        *,
        record: dict[str, Any],
        object_key: str,
        collection_key: str,
        operation: Callable[[], tuple[bool, Any]],
    ) -> dict[str, Any]:
        """Persist a pending job whose mutation runs after one observed pending poll."""
        with self._lock:
            state = _BackgroundJob(
                record=deepcopy(record),
                object_key=object_key,
                collection_key=collection_key,
                operation=operation,
            )
            self._background_jobs[job_id] = state
            self._objects[object_key] = deepcopy(record)
            self._collections.setdefault(collection_key, {})[object_key] = deepcopy(record)
            return deepcopy(record)

    def poll_background_job(self, job_id: int) -> dict[str, Any] | None:
        """Observe pending once, then complete or fail the queued mutation deterministically."""
        with self._lock:
            state = self._background_jobs.get(job_id)
            if state is None:
                return None
            if state.record["status"] != "pending":
                return deepcopy(state.record)
            if state.pending_polls > 0:
                state.pending_polls -= 1
                return deepcopy(state.record)

            try:
                succeeded, result = state.operation()
            except Exception as exc:  # noqa: BLE001 - job failures become observable state
                succeeded, result = False, str(exc)
            state.record["status"] = "completed" if succeeded else "failed"
            state.record["error"] = "" if succeeded else str(result)
            self._objects[state.object_key] = deepcopy(state.record)
            self._collections.setdefault(state.collection_key, {})[state.object_key] = deepcopy(
                state.record
            )
            return deepcopy(state.record)

    # --- Metadata ---

    def stats(self) -> dict[str, int]:
        """Return a snapshot of store sizes."""
        with self._lock:
            return {
                "objects": len(self._objects),
                "collections": len(self._collections),
                "deleted": len(self._deleted),
            }


def _resolved_namespace(namespace: str | None) -> str:
    return namespace or os.environ.get("NETBOX_MOCK_STATE_NAMESPACE", "default")


def _namespace_key(namespace: str, schema_fingerprint: str) -> str:
    digest = hashlib.sha256(f"{namespace}:{schema_fingerprint}".encode()).hexdigest()[:16]
    return f"{namespace}:{digest}"


def mock_store(
    schema_fingerprint: str,
    *,
    namespace: str | None = None,
) -> ThreadSafeMockStore:
    """Return (or create) the singleton store for the given namespace."""
    resolved = _resolved_namespace(namespace)
    cache_key = _namespace_key(resolved, schema_fingerprint)

    with _store_lock:
        if cache_key not in _stores:
            _stores[cache_key] = ThreadSafeMockStore()
        store = _stores[cache_key]

    store.touch_schema(schema_fingerprint)
    return store


def reset_mock_state(*, namespace: str | None = None, schema_fingerprint: str = "") -> None:
    """Reset the live mock state for a given namespace."""
    resolved = namespace or os.environ.get("NETBOX_MOCK_STATE_NAMESPACE")
    with _store_lock:
        stores = (
            _stores.values()
            if resolved is None
            else (store for key, store in _stores.items() if key.startswith(f"{resolved}:"))
        )
        for store in stores:
            store.reset()


__all__ = [
    "ThreadSafeMockStore",
    "mock_store",
    "reset_mock_state",
]
