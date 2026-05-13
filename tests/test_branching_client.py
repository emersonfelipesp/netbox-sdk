"""Tests for :class:`netbox_sdk.branching.BranchingClient` against the mock app.

Exercises the netbox-branching plugin surface end-to-end: feature detection
(installed and missing), CRUD by PK or schema_id, action verbs with optional
job polling, branch events / changes / branchable-models, the activate()
context manager that wires ``X-NetBox-Branch``, and the BranchConflictError
mapping for 409 responses.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
import pytest

from netbox_sdk import (
    BranchConflictError,
    BranchingClient,
    BranchingPluginUnavailableError,
)
from netbox_sdk.client import NetBoxApiClient, _scoped_headers
from netbox_sdk.config import Config
from netbox_sdk.facade import Api
from netbox_sdk.mock import create_mock_app
from netbox_sdk.mock.routes_branching import _reset as _reset_branching

pytestmark = pytest.mark.suite_sdk


@pytest.fixture(autouse=True)
def _isolate_scoped_headers():
    """Reset the shared ``_scoped_headers`` ContextVar around every test.

    Other test modules (e.g. test_branching_cli) drive the CLI's
    ``--branch`` flag which writes ``X-NetBox-Branch`` into this var; if
    pytest-xdist co-locates those tests on the same worker, the residual
    value survives into our ``activate()`` assertions.
    """
    token = _scoped_headers.set({})
    try:
        yield
    finally:
        _scoped_headers.reset(token)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _AsgiClient:
    """aiohttp-shaped async client that talks to the in-process FastAPI app.

    NetBoxApiClient normally uses aiohttp, but for these tests we patch the
    request method to route through httpx's ASGITransport so we don't need a
    bound port. The patch only replaces ``request`` which is the single
    public entrypoint used by :class:`BranchingClient`.
    """

    def __init__(self, app: Any) -> None:
        self._transport = httpx.ASGITransport(app=app)

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=self._transport,
            base_url="http://testserver",
        ) as c:
            return await c.request(
                method,
                path,
                params=params,
                json=json,
                headers=headers,
            )


@pytest.fixture(scope="module")
def app():
    return create_mock_app()


@pytest.fixture
def api(app, monkeypatch):
    """Build an :class:`Api` whose underlying client talks to the ASGI app."""
    _reset_branching()
    os.environ.pop("NETBOX_MOCK_BRANCHING_AVAILABLE", None)

    cfg = Config(base_url="http://testserver", token="dummy", ssl_verify=False)
    raw = NetBoxApiClient(cfg)
    asgi = _AsgiClient(app)

    async def _patched_request(
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,  # noqa: ARG001
    ):
        scoped = _scoped_headers.get() or {}
        merged: dict[str, str] = dict(scoped)
        if headers:
            merged.update(headers)
        # FastAPI body parsing: send JSON only when actual content exists.
        send_body = (
            payload
            if (payload not in (None, {}) or method.upper() in {"POST", "PATCH", "PUT"})
            else None
        )
        response = await asgi.request_json(
            method,
            path,
            params=query,
            json=send_body,
            headers=merged or None,
        )

        class _R:
            def __init__(self, r: httpx.Response) -> None:
                self.status = r.status_code
                self._text = r.text
                self.headers = dict(r.headers)

            @property
            def text(self) -> str:
                return self._text

            def json(self) -> Any:
                import json as _json

                return _json.loads(self._text)

        return _R(response)

    monkeypatch.setattr(raw, "request", _patched_request)
    api = Api(client=raw)
    yield api
    asyncio.get_event_loop().run_until_complete(raw.close()) if False else None


# ---------------------------------------------------------------------------
# Feature detection
# ---------------------------------------------------------------------------


async def test_is_available_when_plugin_installed(api):
    assert await api.branching.is_available() is True


async def test_is_available_when_plugin_missing(api, monkeypatch):
    monkeypatch.setenv("NETBOX_MOCK_BRANCHING_AVAILABLE", "0")
    assert await api.branching.is_available() is False


async def test_branchable_models_returns_list(api):
    rows = await api.branching.branchable_models()
    assert isinstance(rows, list)
    assert rows  # at least one model


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


async def test_create_and_list_branch(api):
    created = await api.branching.create("test-create", description="hello")
    assert created["name"] == "test-create"
    assert created["description"] == "hello"
    assert len(created["schema_id"]) == 8

    rows = await api.branching.list()
    assert any(r["id"] == created["id"] for r in rows)


async def test_get_by_pk_and_schema_id(api):
    b = await api.branching.create("test-lookup")
    by_pk = await api.branching.get(b["id"])
    by_schema = await api.branching.get(b["schema_id"])
    assert by_pk["id"] == by_schema["id"] == b["id"]


async def test_get_by_unknown_schema_id_raises(api):
    with pytest.raises(Exception):
        await api.branching.get("zzzzzzzz")


async def test_update_branch_fields(api):
    b = await api.branching.create("test-update")
    updated = await api.branching.update(b["id"], description="new desc")
    assert updated["description"] == "new desc"


async def test_delete_branch_removes_it(api):
    b = await api.branching.create("test-delete")
    await api.branching.delete(b["id"])
    rows = await api.branching.list()
    assert not any(r["id"] == b["id"] for r in rows)


# ---------------------------------------------------------------------------
# Actions + job polling
# ---------------------------------------------------------------------------


async def test_sync_with_wait_updates_branch(api):
    b = await api.branching.create("test-sync")
    result = await api.branching.sync(b["id"], wait=True, poll_interval=0.01, timeout=2.0)
    assert result["status"]["value"] == "completed"
    refreshed = await api.branching.get(b["id"])
    assert refreshed["last_sync"] is not None


async def test_merge_with_wait_marks_branch_merged(api):
    b = await api.branching.create("test-merge")
    await api.branching.merge(b["id"], wait=True, poll_interval=0.01, timeout=2.0)
    refreshed = await api.branching.get(b["id"])
    assert refreshed["status"]["value"] == "merged"
    assert refreshed["merged_time"] is not None


async def test_sync_without_wait_returns_pending_job(api):
    b = await api.branching.create("test-sync-no-wait")
    result = await api.branching.sync(b["id"], wait=False)
    assert result["status"]["value"] == "pending"


async def test_archive_marks_branch_archived(api):
    b = await api.branching.create("test-archive")
    result = await api.branching.archive(b["id"])
    assert result["status"]["value"] == "archived"


# ---------------------------------------------------------------------------
# Activation context manager
# ---------------------------------------------------------------------------


async def test_activate_sets_branch_header(api):
    b = await api.branching.create("test-activate")
    with api.branching.activate(b["schema_id"]):
        scoped = _scoped_headers.get() or {}
        assert scoped.get("X-NetBox-Branch") == b["schema_id"]
    # After the context exits the header is gone.
    scoped_after = _scoped_headers.get() or {}
    assert "X-NetBox-Branch" not in scoped_after


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------


async def test_branching_unavailable_raises(api, monkeypatch):
    monkeypatch.setenv("NETBOX_MOCK_BRANCHING_AVAILABLE", "0")
    with pytest.raises(BranchingPluginUnavailableError):
        # Any action verb hits a 404 → typed error.
        await api.branching.archive(999)


def test_branch_conflict_error_carries_conflicts():
    conflicts = [{"model": "dcim.device", "id": 1, "reason": "edited on main"}]
    err = BranchConflictError(conflicts)
    assert err.conflicts == conflicts
    assert "conflict" in str(err).lower()


def test_branching_client_constructible_without_facade():
    """BranchingClient should accept any object with a ``client`` attribute."""

    class _FakeApi:
        client = object()

    bc = BranchingClient(_FakeApi())
    assert bc is not None
