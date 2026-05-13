"""In-memory FastAPI routes for the netbox-branching plugin.

Implements the v1.0.x plugin surface (CRUD + sync/merge/revert/archive
actions + branch-events + changes + branchable-models) plus a synthetic
``/api/core/jobs/{id}/`` endpoint so polling helpers terminate.

The routes are intentionally minimal but stateful: branches and events
persist across requests in a per-process dict, and queued action jobs
flip to ``completed`` on the next ``/api/core/jobs/{id}/`` poll so SDK
``wait=True`` loops finish quickly in tests. When the env var
``NETBOX_MOCK_BRANCHING_AVAILABLE`` is set to ``"0"``, the entire plugin
surface returns 404 so feature-detection negative paths can be tested.
"""

from __future__ import annotations

import os
import secrets
import string
import threading
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response

_LOCK = threading.RLock()
_BRANCHES: dict[int, dict[str, Any]] = {}
_NEXT_BRANCH_ID = 1
_EVENTS: list[dict[str, Any]] = []
_CHANGES: list[dict[str, Any]] = []
_JOBS: dict[int, dict[str, Any]] = {}
_NEXT_JOB_ID = 1


_SCHEMA_ALPHABET = string.ascii_lowercase + string.digits
_TERMINAL_STATUSES = {"completed", "errored", "failed", "terminated"}


def _branching_disabled() -> bool:
    return os.environ.get("NETBOX_MOCK_BRANCHING_AVAILABLE", "1") == "0"


def _reset() -> None:
    """Clear branching state (used by ``/mock/reset`` and tests)."""
    global _NEXT_BRANCH_ID, _NEXT_JOB_ID
    with _LOCK:
        _BRANCHES.clear()
        _EVENTS.clear()
        _CHANGES.clear()
        _JOBS.clear()
        _NEXT_BRANCH_ID = 1
        _NEXT_JOB_ID = 1


def _new_schema_id() -> str:
    return "".join(secrets.choice(_SCHEMA_ALPHABET) for _ in range(8))


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _branch_payload(branch: dict[str, Any]) -> dict[str, Any]:
    return dict(branch)


def _queue_job(action: str, branch: dict[str, Any]) -> dict[str, Any]:
    """Create a synthetic job and return its representation."""
    global _NEXT_JOB_ID
    with _LOCK:
        job_id = _NEXT_JOB_ID
        _NEXT_JOB_ID += 1
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
        _JOBS[job_id] = job
        return {k: v for k, v in job.items() if not k.startswith("_")}


def _apply_pending_action(job: dict[str, Any]) -> None:
    """Mutate the underlying branch to reflect a completed action."""
    action = job.get("_pending_action")
    branch_id = job.get("_branch_id")
    if not action or branch_id is None:
        return
    branch = _BRANCHES.get(branch_id)
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
    _EVENTS.append(
        {
            "id": len(_EVENTS) + 1,
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
        ok = True
        for key, expected in params.multi_items():
            if key in {"limit", "offset", "ordering"}:
                continue
            actual = item.get(key)
            if isinstance(actual, dict):
                actual = actual.get("value", actual.get("id"))
            if str(actual) != str(expected):
                ok = False
                break
        if ok:
            result.append(item)
    return result


def _paginate(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"count": len(items), "next": None, "previous": None, "results": items}


def register_branching_mock_routes(app: FastAPI) -> None:
    """Attach netbox-branching plugin routes to a FastAPI app."""

    @app.get("/api/plugins/branching/", include_in_schema=False)
    async def branching_root() -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        return {"message": "netbox-branching mock"}

    @app.get("/api/plugins/branching/branchable-models/", include_in_schema=False)
    async def branchable_models() -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        return _paginate(
            [
                {"app_label": "dcim", "model": "device"},
                {"app_label": "ipam", "model": "prefix"},
            ]
        )

    @app.get("/api/plugins/branching/branches/", include_in_schema=False)
    async def list_branches(request: Request) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            items = [_branch_payload(b) for b in _BRANCHES.values()]
        return _paginate(_list_filtered(items, request))

    @app.post("/api/plugins/branching/branches/", include_in_schema=False)
    async def create_branch(request: Request) -> Response:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        global _NEXT_BRANCH_ID
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        if not isinstance(body, dict) or not body.get("name"):
            raise HTTPException(status_code=400, detail={"name": ["This field is required."]})
        with _LOCK:
            branch_id = _NEXT_BRANCH_ID
            _NEXT_BRANCH_ID += 1
            schema_id = _new_schema_id()
            branch = {
                "id": branch_id,
                "url": f"/api/plugins/branching/branches/{branch_id}/",
                "schema_id": schema_id,
                "name": str(body["name"]),
                "description": str(body.get("description", "")),
                "comments": str(body.get("comments", "")),
                "status": {"value": "ready", "label": "Ready"},
                "created": _now_iso(),
                "last_sync": None,
                "merged_time": None,
                "owner": None,
            }
            _BRANCHES[branch_id] = branch
            _EVENTS.append(
                {
                    "id": len(_EVENTS) + 1,
                    "branch": branch_id,
                    "type": "provisioned",
                    "user": {"id": 1, "username": "mock", "display": "mock"},
                    "time": branch["created"],
                }
            )
            payload = _branch_payload(branch)
        return Response(
            content=__import__("json").dumps(payload),
            status_code=201,
            media_type="application/json",
        )

    @app.get("/api/plugins/branching/branches/{branch_id}/", include_in_schema=False)
    async def get_branch(branch_id: int) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            branch = _BRANCHES.get(branch_id)
            if branch is None:
                raise HTTPException(status_code=404, detail="Not found.")
            return _branch_payload(branch)

    @app.patch("/api/plugins/branching/branches/{branch_id}/", include_in_schema=False)
    async def update_branch(branch_id: int, request: Request) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        try:
            body = await request.json()
        except Exception:  # noqa: BLE001
            body = {}
        with _LOCK:
            branch = _BRANCHES.get(branch_id)
            if branch is None:
                raise HTTPException(status_code=404, detail="Not found.")
            if isinstance(body, dict):
                for field in ("name", "description", "comments"):
                    if field in body and body[field] is not None:
                        branch[field] = str(body[field])
            return _branch_payload(branch)

    @app.delete("/api/plugins/branching/branches/{branch_id}/", include_in_schema=False)
    async def delete_branch(branch_id: int) -> Response:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            if branch_id not in _BRANCHES:
                raise HTTPException(status_code=404, detail="Not found.")
            _BRANCHES.pop(branch_id)
        return Response(status_code=204)

    async def _action_route(branch_id: int, action: str) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            branch = _BRANCHES.get(branch_id)
            if branch is None:
                raise HTTPException(status_code=404, detail="Not found.")
            return _queue_job(action, branch)

    @app.post("/api/plugins/branching/branches/{branch_id}/sync/", include_in_schema=False)
    async def sync_branch(branch_id: int) -> dict[str, Any]:
        return await _action_route(branch_id, "sync")

    @app.post("/api/plugins/branching/branches/{branch_id}/merge/", include_in_schema=False)
    async def merge_branch(branch_id: int) -> dict[str, Any]:
        return await _action_route(branch_id, "merge")

    @app.post("/api/plugins/branching/branches/{branch_id}/revert/", include_in_schema=False)
    async def revert_branch(branch_id: int) -> dict[str, Any]:
        return await _action_route(branch_id, "revert")

    @app.post("/api/plugins/branching/branches/{branch_id}/archive/", include_in_schema=False)
    async def archive_branch(branch_id: int) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            branch = _BRANCHES.get(branch_id)
            if branch is None:
                raise HTTPException(status_code=404, detail="Not found.")
            branch["status"] = {"value": "archived", "label": "Archived"}
            return _branch_payload(branch)

    @app.get("/api/plugins/branching/branch-events/", include_in_schema=False)
    async def list_branch_events(request: Request) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            items = list(_EVENTS)
        return _paginate(_list_filtered(items, request))

    @app.get("/api/plugins/branching/changes/", include_in_schema=False)
    async def list_changes(request: Request) -> dict[str, Any]:
        if _branching_disabled():
            raise HTTPException(status_code=404)
        with _LOCK:
            items = list(_CHANGES)
        return _paginate(_list_filtered(items, request))

    @app.get("/api/core/jobs/{job_id}/", include_in_schema=False)
    async def get_job(job_id: int) -> dict[str, Any]:
        with _LOCK:
            job = _JOBS.get(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail="Not found.")
            status = job["status"]["value"]
            if status not in _TERMINAL_STATUSES:
                _apply_pending_action(job)
                job["status"] = {"value": "completed", "label": "Completed"}
                job["started"] = job.get("started") or _now_iso()
                job["completed"] = _now_iso()
            return {k: v for k, v in job.items() if not k.startswith("_")}


__all__ = ["register_branching_mock_routes", "_reset"]
