"""In-memory FastAPI routes for the netbox-branching plugin.

Implements the v1.0.x plugin surface (CRUD + sync/merge/revert/archive
actions + branch-events + changes + branchable-models) plus a synthetic
``/api/core/jobs/{id}/`` endpoint so polling helpers terminate.

Each route registration owns its branching state. Queued action jobs flip to
``completed`` on the next ``/api/core/jobs/{id}/`` poll so SDK ``wait=True``
loops finish quickly in tests. When ``NETBOX_MOCK_BRANCHING_AVAILABLE`` is
``"0"``, the entire plugin surface returns 404 so feature-detection negative
paths can be tested.
"""

from __future__ import annotations

import json
import os
import secrets
import string
import threading
import time
import weakref
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response

from netbox_sdk.mock.state import ThreadSafeMockStore

_SCHEMA_ALPHABET = string.ascii_lowercase + string.digits
_TERMINAL_STATUSES = {"completed", "errored", "failed", "terminated"}


class BranchingMockState:
    """Mutable branching data owned by one mock application."""

    def __init__(self, *, background_job_store: ThreadSafeMockStore | None = None) -> None:
        self.lock = threading.RLock()
        self.branches: dict[int, dict[str, Any]] = {}
        self.next_branch_id = 1
        self.events: list[dict[str, Any]] = []
        self.changes: list[dict[str, Any]] = []
        self.jobs: dict[int, dict[str, Any]] = {}
        self.next_job_id = 1
        self.background_job_store = background_job_store

    def reset(self) -> None:
        """Clear only this application's branching state."""
        with self.lock:
            self.branches.clear()
            self.events.clear()
            self.changes.clear()
            self.jobs.clear()
            self.next_branch_id = 1
            self.next_job_id = 1

    def allocate_branch_id(self) -> int:
        """Return the next application-local branch ID."""
        with self.lock:
            branch_id = self.next_branch_id
            self.next_branch_id += 1
            return branch_id

    def queue_job(self, action: str, branch: dict[str, Any]) -> dict[str, Any]:
        """Create a synthetic application-local job and return its representation."""
        with self.lock:
            if self.background_job_store is None:
                job_id = self.next_job_id
                self.next_job_id += 1
            else:
                job_id = self.background_job_store.next_id("/api/core/jobs/")
            job = {
                "id": job_id,
                "url": f"/api/core/jobs/{job_id}/",
                "object_type": "netbox_branching.branch",
                "object_id": branch["id"],
                "name": action,
                "status": {"value": "pending", "label": "Pending"},
                "created": _now_iso(),
                "started": None,
                "completed": None,
                "user": {"id": 1, "username": "mock", "display": "mock"},
                "data": {"branch_id": branch["id"], "branch_schema_id": branch["schema_id"]},
                "error": "",
                "_pending_action": action,
                "_branch_id": branch["id"],
            }
            self.jobs[job_id] = job
            return _public_job(job)


_REGISTERED_STATES: weakref.WeakSet[BranchingMockState] = weakref.WeakSet()


def _branching_disabled() -> bool:
    return os.environ.get("NETBOX_MOCK_BRANCHING_AVAILABLE", "1") == "0"


def _reset() -> None:
    """Clear every live registered state for backward-compatible test setup."""
    for state in tuple(_REGISTERED_STATES):
        state.reset()


def _new_schema_id() -> str:
    return "".join(secrets.choice(_SCHEMA_ALPHABET) for _ in range(8))


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _branch_payload(branch: dict[str, Any]) -> dict[str, Any]:
    return dict(branch)


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in job.items() if not key.startswith("_")}


def _apply_pending_action(state: BranchingMockState, job: dict[str, Any]) -> None:
    """Mutate the underlying branch to reflect a completed action."""
    action = job.get("_pending_action")
    branch_id = job.get("_branch_id")
    if not action or branch_id is None:
        return
    branch = state.branches.get(branch_id)
    if branch is None:
        return

    now = _now_iso()
    if action == "sync":
        branch["status"] = {"value": "ready", "label": "Ready"}
        branch["last_sync"] = now
    elif action == "merge":
        branch["status"] = {"value": "merged", "label": "Merged"}
        branch["merged_time"] = now
    elif action == "revert":
        branch["status"] = {"value": "ready", "label": "Ready"}
        branch["merged_time"] = None
    state.events.append(
        {
            "id": len(state.events) + 1,
            "branch": branch_id,
            "type": action + "ed",
            "user": {"id": 1, "username": "mock", "display": "mock"},
            "time": now,
        }
    )


def _list_filtered(items: list[dict[str, Any]], request: Request) -> list[dict[str, Any]]:
    params = request.query_params
    if not params:
        return list(items)
    result: list[dict[str, Any]] = []
    for item in items:
        matches = True
        for key, expected in params.multi_items():
            if key in {"limit", "offset", "ordering"}:
                continue
            actual = item.get(key)
            if isinstance(actual, dict):
                actual = actual.get("value", actual.get("id"))
            if str(actual) != str(expected):
                matches = False
                break
        if matches:
            result.append(item)
    return result


def _paginate(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"count": len(items), "next": None, "previous": None, "results": items}


class BranchingMockRoutes:
    """Bound FastAPI handlers for one application's branching state."""

    def __init__(self, state: BranchingMockState) -> None:
        self.state = state

    async def branching_root(self) -> dict[str, Any]:
        self._require_available()
        return {"message": "netbox-branching mock"}

    async def branchable_models(self) -> dict[str, Any]:
        self._require_available()
        return _paginate(
            [
                {"app_label": "dcim", "model": "device"},
                {"app_label": "ipam", "model": "prefix"},
            ]
        )

    async def list_branches(self, request: Request) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            items = [_branch_payload(branch) for branch in self.state.branches.values()]
        return _paginate(_list_filtered(items, request))

    async def create_branch(self, request: Request) -> Response:
        self._require_available()
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        if not isinstance(body, dict) or not body.get("name"):
            raise HTTPException(status_code=400, detail={"name": ["This field is required."]})
        with self.state.lock:
            branch_id = self.state.allocate_branch_id()
            branch = {
                "id": branch_id,
                "url": f"/api/plugins/branching/branches/{branch_id}/",
                "schema_id": _new_schema_id(),
                "name": str(body["name"]),
                "description": str(body.get("description", "")),
                "comments": str(body.get("comments", "")),
                "status": {"value": "ready", "label": "Ready"},
                "created": _now_iso(),
                "last_sync": None,
                "merged_time": None,
                "owner": None,
            }
            self.state.branches[branch_id] = branch
            self.state.events.append(
                {
                    "id": len(self.state.events) + 1,
                    "branch": branch_id,
                    "type": "provisioned",
                    "user": {"id": 1, "username": "mock", "display": "mock"},
                    "time": branch["created"],
                }
            )
        return Response(
            content=json.dumps(_branch_payload(branch)),
            status_code=201,
            media_type="application/json",
        )

    async def get_branch(self, branch_id: int) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            return _branch_payload(self._get_branch(branch_id))

    async def update_branch(self, branch_id: int, request: Request) -> dict[str, Any]:
        self._require_available()
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        with self.state.lock:
            branch = self._get_branch(branch_id)
            if isinstance(body, dict):
                for field in ("name", "description", "comments"):
                    if field in body and body[field] is not None:
                        branch[field] = str(body[field])
            return _branch_payload(branch)

    async def delete_branch(self, branch_id: int) -> Response:
        self._require_available()
        with self.state.lock:
            self._get_branch(branch_id)
            self.state.branches.pop(branch_id)
        return Response(status_code=204)

    async def sync_branch(self, branch_id: int) -> dict[str, Any]:
        return self._queue_action(branch_id, "sync")

    async def merge_branch(self, branch_id: int) -> dict[str, Any]:
        return self._queue_action(branch_id, "merge")

    async def revert_branch(self, branch_id: int) -> dict[str, Any]:
        return self._queue_action(branch_id, "revert")

    async def archive_branch(self, branch_id: int) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            branch = self._get_branch(branch_id)
            branch["status"] = {"value": "archived", "label": "Archived"}
            return _branch_payload(branch)

    async def list_branch_events(self, request: Request) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            items = list(self.state.events)
        return _paginate(_list_filtered(items, request))

    async def list_changes(self, request: Request) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            items = list(self.state.changes)
        return _paginate(_list_filtered(items, request))

    async def get_job(self, job_id: int) -> dict[str, Any]:
        with self.state.lock:
            job = self.state.jobs.get(job_id)
            if job is not None:
                return self._poll_branch_job(job)
        background_store = self.state.background_job_store
        background_job = background_store.poll_background_job(job_id) if background_store else None
        if background_job is None:
            raise HTTPException(status_code=404, detail="Not found.")
        return background_job

    def _queue_action(self, branch_id: int, action: str) -> dict[str, Any]:
        self._require_available()
        with self.state.lock:
            return self.state.queue_job(action, self._get_branch(branch_id))

    def _poll_branch_job(self, job: dict[str, Any]) -> dict[str, Any]:
        status = job["status"]["value"]
        if status not in _TERMINAL_STATUSES:
            _apply_pending_action(self.state, job)
            job["status"] = {"value": "completed", "label": "Completed"}
            job["started"] = job.get("started") or _now_iso()
            job["completed"] = _now_iso()
        return _public_job(job)

    def _get_branch(self, branch_id: int) -> dict[str, Any]:
        branch = self.state.branches.get(branch_id)
        if branch is None:
            raise HTTPException(status_code=404, detail="Not found.")
        return branch

    @staticmethod
    def _require_available() -> None:
        if _branching_disabled():
            raise HTTPException(status_code=404)


def register_branching_mock_routes(
    app: FastAPI,
    *,
    background_job_store: ThreadSafeMockStore | None = None,
    state: BranchingMockState | None = None,
) -> BranchingMockState:
    """Attach isolated netbox-branching plugin routes to a FastAPI app."""
    active_state = state or BranchingMockState(background_job_store=background_job_store)
    _REGISTERED_STATES.add(active_state)
    handlers = BranchingMockRoutes(active_state)
    routes = (
        ("/api/plugins/branching/", handlers.branching_root, "GET"),
        ("/api/plugins/branching/branchable-models/", handlers.branchable_models, "GET"),
        ("/api/plugins/branching/branches/", handlers.list_branches, "GET"),
        ("/api/plugins/branching/branches/", handlers.create_branch, "POST"),
        ("/api/plugins/branching/branches/{branch_id}/", handlers.get_branch, "GET"),
        ("/api/plugins/branching/branches/{branch_id}/", handlers.update_branch, "PATCH"),
        ("/api/plugins/branching/branches/{branch_id}/", handlers.delete_branch, "DELETE"),
        ("/api/plugins/branching/branches/{branch_id}/sync/", handlers.sync_branch, "POST"),
        ("/api/plugins/branching/branches/{branch_id}/merge/", handlers.merge_branch, "POST"),
        ("/api/plugins/branching/branches/{branch_id}/revert/", handlers.revert_branch, "POST"),
        ("/api/plugins/branching/branches/{branch_id}/archive/", handlers.archive_branch, "POST"),
        ("/api/plugins/branching/branch-events/", handlers.list_branch_events, "GET"),
        ("/api/plugins/branching/changes/", handlers.list_changes, "GET"),
        ("/api/core/jobs/{job_id}/", handlers.get_job, "GET"),
    )
    for path, endpoint, method in routes:
        app.add_api_route(path, endpoint, methods=[method], include_in_schema=False)
    return active_state


__all__ = ["BranchingMockState", "register_branching_mock_routes", "_reset"]
