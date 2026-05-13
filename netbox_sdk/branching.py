"""High-level client for the ``netbox-branching`` plugin.

This module wraps the plugin's REST surface so callers can branch, sync,
merge, revert, and archive NetBox database branches without composing
raw HTTP requests. It also exposes a ``activate()`` context manager that
delegates to :meth:`netbox_sdk.client.NetBoxApiClient.header_scope` so
all in-block requests carry the ``X-NetBox-Branch`` header.

The plugin's authoritative paths (matching ``netboxlabs-netbox-branching``
v1.0.3) are:

* ``/api/plugins/branching/branches/``                   — CRUD
* ``/api/plugins/branching/branches/{id}/sync/``          — POST action
* ``/api/plugins/branching/branches/{id}/merge/``         — POST action
* ``/api/plugins/branching/branches/{id}/revert/``        — POST action
* ``/api/plugins/branching/branches/{id}/archive/``       — POST action
* ``/api/plugins/branching/branch-events/``               — read
* ``/api/plugins/branching/changes/``                     — read
* ``/api/plugins/branching/branchable-models/``           — read
* ``/api/core/jobs/{id}/``                                — job polling

Sync/merge/revert all return a queued :class:`Job`; pass ``wait=True``
(or call :meth:`BranchingClient.wait_for_job`) to block until it
terminates. Conflicts surface as :class:`BranchConflictError`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, cast

from netbox_sdk.exceptions import (
    BranchConflictError,
    BranchingPluginUnavailableError,
    BranchJobTimeoutError,
    ContentError,
    RequestError,
)

if TYPE_CHECKING:
    from netbox_sdk.client import ApiResponse
    from netbox_sdk.facade import Api

logger = logging.getLogger(__name__)

# ``BranchingClient.list`` shadows the builtin ``list`` in class-scope
# annotations. Bind the builtin to a private alias so return types like
# ``_BuiltinList[dict[str, Any]]`` resolve correctly under static type
# checkers (ty).
_BuiltinList = list

_SCHEMA_ID_RE = re.compile(r"^[a-z0-9]{8}$")
_TERMINAL_JOB_STATUSES = frozenset({"completed", "errored", "failed", "terminated"})
_DEFAULT_POLL_INTERVAL = 2.0
_DEFAULT_TIMEOUT = 300.0


def _decode_json(response: ApiResponse) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError as exc:
        raise ContentError(response) from exc


def _raise_for_status(response: ApiResponse) -> None:
    if 200 <= response.status < 300:
        return
    raise RequestError(response)


def _is_schema_id(value: str) -> bool:
    return bool(_SCHEMA_ID_RE.match(value))


def _branch_label(branch: Any) -> str | int | None:
    """Pick the most useful identifier from a branch-like object."""
    if branch is None:
        return None
    for attr in ("schema_id", "id", "pk", "name"):
        value = getattr(branch, attr, None)
        if value is not None:
            return value
    if isinstance(branch, dict):
        for key in ("schema_id", "id", "pk", "name"):
            value = branch.get(key)
            if value is not None:
                return value
    return None


class BranchingClient:
    """Ergonomic accessor for the ``netbox-branching`` plugin.

    Construct via :attr:`netbox_sdk.facade.Api.branching` or directly with
    an existing :class:`~netbox_sdk.facade.Api` handle. All methods are
    coroutines except :meth:`activate`, which is a synchronous context
    manager wrapping :meth:`netbox_sdk.client.NetBoxApiClient.header_scope`.
    """

    BASE = "/api/plugins/branching"

    def __init__(self, api: Api) -> None:
        self._api = api
        self._client = api.client

    # ------------------------------------------------------------------
    # Feature detection
    # ------------------------------------------------------------------
    async def is_available(self) -> bool:
        """Return ``True`` if the branching plugin is installed on the server."""
        response = await self._client.request("GET", f"{self.BASE}/")
        if response.status == 404:
            return False
        if 200 <= response.status < 300:
            return True
        # Other failures (auth, network) — surface them.
        raise RequestError(response)

    async def branchable_models(self) -> _BuiltinList[dict[str, Any]]:
        """List the NetBox models that participate in branching."""
        response = await self._client.request("GET", f"{self.BASE}/branchable-models/")
        _raise_for_status(response)
        payload = _decode_json(response)
        if isinstance(payload, dict) and "results" in payload:
            results = payload["results"]
            if isinstance(results, list):
                return cast("list[dict[str, Any]]", list(results))
        if isinstance(payload, list):
            return cast("list[dict[str, Any]]", list(payload))
        raise ContentError(response)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def list(self, **filters: Any) -> _BuiltinList[dict[str, Any]]:
        """Return the list of branches matching ``filters`` (server-side query)."""
        return await self._list(f"{self.BASE}/branches/", filters)

    async def get(self, id_or_schema: int | str) -> dict[str, Any]:
        """Fetch a single branch by primary key or ``schema_id``."""
        pk = await self._resolve_pk(id_or_schema)
        response = await self._client.request("GET", f"{self.BASE}/branches/{pk}/")
        _raise_for_status(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        return payload

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        """Find a branch by ``name``; returns ``None`` when nothing matches."""
        results = await self._list(f"{self.BASE}/branches/", {"name": name})
        for entry in results:
            if entry.get("name") == name:
                return entry
        return None

    async def create(self, name: str, **fields: Any) -> dict[str, Any]:
        """Create a branch with the given name and optional extra fields."""
        body: dict[str, Any] = {"name": name, **fields}
        response = await self._client.request("POST", f"{self.BASE}/branches/", payload=body)
        self._raise_branching(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        return payload

    async def update(self, id_or_schema: int | str, **fields: Any) -> dict[str, Any]:
        """Patch a branch's metadata."""
        pk = await self._resolve_pk(id_or_schema)
        response = await self._client.request(
            "PATCH", f"{self.BASE}/branches/{pk}/", payload=fields
        )
        self._raise_branching(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        return payload

    async def delete(self, id_or_schema: int | str) -> None:
        """Delete a branch."""
        pk = await self._resolve_pk(id_or_schema)
        response = await self._client.request("DELETE", f"{self.BASE}/branches/{pk}/")
        self._raise_branching(response)

    # ------------------------------------------------------------------
    # Action verbs
    # ------------------------------------------------------------------
    async def sync(
        self,
        id_or_schema: int | str,
        *,
        commit: bool = True,
        acknowledge_conflicts: bool = False,
        wait: bool = False,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        timeout: float | None = _DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Queue a sync of the branch with ``main`` (returns the queued job)."""
        return await self._action(
            id_or_schema,
            "sync",
            {"commit": commit, "acknowledge_conflicts": acknowledge_conflicts},
            wait=wait,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    async def merge(
        self,
        id_or_schema: int | str,
        *,
        commit: bool = True,
        acknowledge_conflicts: bool = False,
        wait: bool = False,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        timeout: float | None = _DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Queue a merge of the branch into ``main`` (returns the queued job)."""
        return await self._action(
            id_or_schema,
            "merge",
            {"commit": commit, "acknowledge_conflicts": acknowledge_conflicts},
            wait=wait,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    async def revert(
        self,
        id_or_schema: int | str,
        *,
        wait: bool = False,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        timeout: float | None = _DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Queue a revert of the branch's previously-merged changes."""
        return await self._action(
            id_or_schema,
            "revert",
            None,
            wait=wait,
            poll_interval=poll_interval,
            timeout=timeout,
        )

    async def archive(self, id_or_schema: int | str) -> dict[str, Any]:
        """Archive the branch (synchronous server-side; returns the updated branch)."""
        pk = await self._resolve_pk(id_or_schema)
        response = await self._client.request(
            "POST", f"{self.BASE}/branches/{pk}/archive/", payload={}
        )
        self._raise_branching(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        return payload

    # ------------------------------------------------------------------
    # Read-only collections
    # ------------------------------------------------------------------
    async def events(self, **filters: Any) -> _BuiltinList[dict[str, Any]]:
        """List branch events matching ``filters``."""
        return await self._list(f"{self.BASE}/branch-events/", filters)

    async def changes(self, **filters: Any) -> _BuiltinList[dict[str, Any]]:
        """List recorded change-diffs matching ``filters``."""
        return await self._list(f"{self.BASE}/changes/", filters)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def wait_for_job(
        self,
        job_id: int,
        *,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        timeout: float | None = _DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Poll ``/api/core/jobs/{id}/`` until terminal status or ``timeout`` elapses."""
        deadline = None if timeout is None else time.monotonic() + timeout
        last: dict[str, Any] = {}
        last_status: str | None = None
        while True:
            response = await self._client.request("GET", f"/api/core/jobs/{job_id}/")
            _raise_for_status(response)
            payload = _decode_json(response)
            if not isinstance(payload, dict):
                raise ContentError(response)
            last = payload
            status_value = payload.get("status")
            if isinstance(status_value, dict):
                last_status = str(status_value.get("value") or status_value.get("label") or "")
            elif status_value is not None:
                last_status = str(status_value)
            if last_status and last_status.lower() in _TERMINAL_JOB_STATUSES:
                return last
            if deadline is not None and time.monotonic() >= deadline:
                raise BranchJobTimeoutError(job_id, last_status)
            await asyncio.sleep(poll_interval)

    @contextmanager
    def activate(self, branch_or_schema_id: Any) -> Iterator[Api]:
        """Activate a branch for every request in the with-block.

        Accepts an integer PK, an 8-char ``schema_id`` string, a branch name
        (must be already loaded; lookup is not performed here), or any object
        exposing a ``schema_id`` attribute. Delegates to
        :meth:`netbox_sdk.client.NetBoxApiClient.header_scope`, so the
        ``X-NetBox-Branch`` header is scoped to the current asyncio task.
        """
        schema_id = self._extract_schema_id(branch_or_schema_id)
        if not schema_id:
            raise ValueError(
                "activate() requires a schema_id, an int PK, or an object with .schema_id"
            )
        with self._client.header_scope(**{"X-NetBox-Branch": schema_id}):
            yield self._api

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _list(self, path: str, filters: dict[str, Any]) -> _BuiltinList[dict[str, Any]]:
        query = {k: v for k, v in filters.items() if v is not None} or None
        response = await self._client.request("GET", path, query=query)
        if response.status == 404:
            raise BranchingPluginUnavailableError()
        _raise_for_status(response)
        payload = _decode_json(response)
        if isinstance(payload, dict) and "results" in payload:
            results = payload["results"]
            if isinstance(results, list):
                return cast("list[dict[str, Any]]", list(results))
        if isinstance(payload, list):
            return cast("list[dict[str, Any]]", list(payload))
        raise ContentError(response)

    async def _action(
        self,
        id_or_schema: int | str,
        verb: str,
        body: dict[str, Any] | None,
        *,
        wait: bool,
        poll_interval: float,
        timeout: float | None,
    ) -> dict[str, Any]:
        pk = await self._resolve_pk(id_or_schema)
        response = await self._client.request(
            "POST",
            f"{self.BASE}/branches/{pk}/{verb}/",
            payload=body if body is not None else {},
        )
        self._raise_branching(response)
        payload = _decode_json(response)
        if not isinstance(payload, dict):
            raise ContentError(response)
        if wait:
            job_id = self._job_id(payload)
            if job_id is None:
                return payload
            return await self.wait_for_job(job_id, poll_interval=poll_interval, timeout=timeout)
        return payload

    async def _resolve_pk(self, id_or_schema: int | str) -> int:
        if isinstance(id_or_schema, int):
            return id_or_schema
        text = str(id_or_schema).strip()
        if text.isdigit():
            return int(text)
        if not _is_schema_id(text):
            raise ValueError(
                f"Branch identifier must be int PK or 8-char schema_id, got {id_or_schema!r}"
            )
        results = await self._list(f"{self.BASE}/branches/", {"schema_id": text})
        for entry in results:
            if entry.get("schema_id") == text:
                pk = entry.get("id") or entry.get("pk")
                if isinstance(pk, int):
                    return pk
        raise ValueError(f"No branch found with schema_id={text!r}")

    @staticmethod
    def _extract_schema_id(branch: Any) -> str | None:
        if branch is None:
            return None
        if isinstance(branch, str):
            return branch.strip() or None
        if isinstance(branch, int):
            return str(branch)
        for attr in ("schema_id", "id", "pk"):
            value = getattr(branch, attr, None)
            if value is not None:
                return str(value)
        if isinstance(branch, dict):
            for key in ("schema_id", "id", "pk"):
                value = branch.get(key)
                if value is not None:
                    return str(value)
        return None

    @staticmethod
    def _job_id(payload: dict[str, Any]) -> int | None:
        # Nested {"job": {...}} shape (older / wrapper responses).
        job = payload.get("job")
        if isinstance(job, dict):
            value = job.get("id") or job.get("pk")
            if isinstance(value, int):
                return value
        # Explicit job_id field.
        value = payload.get("job_id")
        if isinstance(value, int):
            return value
        # Top-level Job representation (sync/merge/revert default shape):
        # disambiguate by checking the URL or object_type so we don't
        # accidentally return a branch PK.
        url = payload.get("url")
        if isinstance(url, str) and "/jobs/" in url:
            value = payload.get("id") or payload.get("pk")
            if isinstance(value, int):
                return value
        object_type = payload.get("object_type")
        if isinstance(object_type, str) and "branch" in object_type:
            value = payload.get("id") or payload.get("pk")
            if isinstance(value, int):
                return value
        return None

    def _raise_branching(self, response: ApiResponse) -> None:
        if 200 <= response.status < 300:
            return
        if response.status == 404:
            raise BranchingPluginUnavailableError()
        if response.status == 409:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = response.text
            conflicts: Any
            if isinstance(payload, dict):
                conflicts = payload.get("conflicts") or payload.get("detail") or payload
            else:
                conflicts = payload
            raise BranchConflictError(conflicts, response=response)
        raise RequestError(response)


__all__ = [
    "BranchingClient",
    "BranchConflictError",
    "BranchingPluginUnavailableError",
    "BranchJobTimeoutError",
]
