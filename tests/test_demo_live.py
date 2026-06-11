"""Live integration tests against demo.netbox.dev.

These tests are skipped unless the ``NETBOX_DEMO_LIVE=1`` environment variable
is set.  They also require ``DEMO_USERNAME`` and ``DEMO_PASSWORD`` so that the
Playwright-based account provisioner can obtain a real API token.

Destructive operations (create / update / patch / delete) are explicitly
permitted on demo.netbox.dev because the demo instance resets periodically and
the test account owns its own objects.

Usage::

    NETBOX_DEMO_LIVE=1 \\
    DEMO_USERNAME=myuser \\
    DEMO_PASSWORD=mypass \\
    uv run pytest tests/test_demo_live.py -v -s
"""

from __future__ import annotations

import json
import os
import uuid

import pytest
from typer.testing import CliRunner

import netbox_cli.demo as cli_demo
from netbox_cli import cli
from netbox_cli.runtime import _get_client_for_config
from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config
from netbox_sdk.demo_auth import bootstrap_demo_profile
from netbox_sdk.schema import build_schema_index
from netbox_sdk.services import list_all_pages, run_dynamic_command

pytestmark = pytest.mark.demo_live

_SKIP_IF_NOT_LIVE = "NETBOX_DEMO_LIVE=1 not set — live demo test skipped"
_SKIP_IF_NO_CREDS = "DEMO_USERNAME / DEMO_PASSWORD not set — live demo test skipped"

# ---------------------------------------------------------------------------
# Session-scoped fixtures — one Playwright run per test session
# ---------------------------------------------------------------------------


def _require_live() -> None:
    if not os.getenv("NETBOX_DEMO_LIVE"):
        pytest.skip(_SKIP_IF_NOT_LIVE)


def _require_credentials() -> tuple[str, str]:
    username = os.getenv("DEMO_USERNAME", "")
    password = os.getenv("DEMO_PASSWORD", "")
    if not username or not password:
        pytest.skip(_SKIP_IF_NO_CREDS)
    return username, password


@pytest.fixture(scope="session")
def demo_cfg() -> Config:
    """Provision a real demo.netbox.dev API token via Playwright (once per session)."""
    _require_live()
    username, password = _require_credentials()
    token_name = f"nbx-live-test-{uuid.uuid4().hex[:8]}"
    return bootstrap_demo_profile(
        username=username,
        password=password,
        timeout=60.0,
        headless=True,
        token_name=token_name,
    )


@pytest.fixture(scope="session")
def live_client(demo_cfg: Config) -> NetBoxApiClient:
    """Return an authenticated NetBoxApiClient against demo.netbox.dev."""
    return _get_client_for_config(demo_cfg)


@pytest.fixture(scope="session")
def live_schema():
    """Return the bundled schema index (sufficient for dynamic command resolution)."""
    return build_schema_index()


# ---------------------------------------------------------------------------
# Helper – run a single dynamic command and return the parsed response body
# ---------------------------------------------------------------------------


async def _run(
    client: NetBoxApiClient,
    schema,
    group: str,
    resource: str,
    action: str,
    *,
    object_id: int | None = None,
    body: dict | list | None = None,
    query: list[str] | None = None,
) -> dict | list:
    response = await run_dynamic_command(
        client=client,
        index=schema,
        group=group,
        resource=resource,
        action=action,
        object_id=object_id,
        query_pairs=query or [],
        body_json=json.dumps(body) if body is not None else None,
        body_file=None,
    )
    assert response.status < 300, (
        f"{action.upper()} {group}/{resource} failed with HTTP {response.status}: "
        f"{response.text[:200]}"
    )
    if response.text:
        return json.loads(response.text)
    return {}


# ---------------------------------------------------------------------------
# 1. Connection smoke-test
# ---------------------------------------------------------------------------


async def test_live_connection(live_client: NetBoxApiClient) -> None:
    """Verify we can reach demo.netbox.dev and receive a valid /api/status/ response."""
    probe = await live_client.probe_connection()
    assert probe.ok, f"demo.netbox.dev not reachable: {probe}"


# ---------------------------------------------------------------------------
# 2. List (basic)
# ---------------------------------------------------------------------------


async def test_live_list_tags(live_client: NetBoxApiClient, live_schema) -> None:
    """GET /api/extras/tags/ returns a paginated envelope with count ≥ 0."""
    data = await _run(live_client, live_schema, "extras", "tags", "list")
    assert isinstance(data, dict), "Expected a paginated envelope"
    assert "count" in data or "results" in data


# ---------------------------------------------------------------------------
# 3. Filter discovery (local – no HTTP request)
# ---------------------------------------------------------------------------


def test_live_filter_discovery(live_schema) -> None:
    """Filter discovery for extras/tags returns at least one filter parameter."""
    _require_live()
    filters = live_schema.filter_params("extras", "tags")
    assert len(filters) > 0, "extras/tags should expose filter parameters"
    names = {f.name for f in filters}
    # Name-based filtering is universally available on list resources
    assert "name" in names or "q" in names


# ---------------------------------------------------------------------------
# 4. Full single-object CRUD lifecycle
# ---------------------------------------------------------------------------


async def test_live_crud_lifecycle(live_client: NetBoxApiClient, live_schema) -> None:
    """Create → get → patch → delete a tag.  Cleans up even on failure."""
    tag_name = f"nbx-test-{uuid.uuid4().hex[:10]}"
    tag_slug = tag_name

    # CREATE
    created = await _run(
        live_client,
        live_schema,
        "extras",
        "tags",
        "create",
        body={"name": tag_name, "slug": tag_slug, "color": "aa1409"},
    )
    assert isinstance(created, dict)
    assert created.get("name") == tag_name
    tag_id: int = created["id"]

    try:
        # GET
        fetched = await _run(live_client, live_schema, "extras", "tags", "get", object_id=tag_id)
        assert fetched["id"] == tag_id
        assert fetched["name"] == tag_name

        # PATCH (single-object PATCH to detail path)
        patched = await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "patch",
            object_id=tag_id,
            body={"color": "0c7a00"},
        )
        assert patched.get("color") == "0c7a00"

        # UPDATE (single-object PUT to detail path)
        updated = await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "update",
            object_id=tag_id,
            body={"name": tag_name, "slug": tag_slug, "color": "ff0000"},
        )
        assert updated.get("color") == "ff0000"

    finally:
        # DELETE – always clean up
        await _run(live_client, live_schema, "extras", "tags", "delete", object_id=tag_id)


# ---------------------------------------------------------------------------
# 5. Bulk operations
# ---------------------------------------------------------------------------


async def test_live_bulk_operations(live_client: NetBoxApiClient, live_schema) -> None:
    """Create 3 tags, bulk-patch them, bulk-update them, then bulk-delete."""
    prefix = f"bulk-{uuid.uuid4().hex[:6]}"
    names = [f"{prefix}-{i}" for i in range(3)]
    slugs = names

    # Create 3 tags individually
    created_ids: list[int] = []
    for name, slug in zip(names, slugs):
        result = await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "create",
            body={"name": name, "slug": slug, "color": "aa1409"},
        )
        created_ids.append(result["id"])

    assert len(created_ids) == 3

    try:
        # BULK-PATCH — PATCH to list path with array body
        patch_payload = [{"id": oid, "color": "0c7a00"} for oid in created_ids]
        bulk_patched = await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "bulk-patch",
            body=patch_payload,
        )
        assert isinstance(bulk_patched, list)
        assert len(bulk_patched) == 3
        assert all(obj.get("color") == "0c7a00" for obj in bulk_patched)

        # BULK-UPDATE — PUT to list path with array body (full replacement)
        update_payload = [
            {"id": oid, "name": names[i], "slug": slugs[i], "color": "ff0000"}
            for i, oid in enumerate(created_ids)
        ]
        bulk_updated = await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "bulk-update",
            body=update_payload,
        )
        assert isinstance(bulk_updated, list)
        assert len(bulk_updated) == 3

    finally:
        # BULK-DELETE — DELETE to list path with array body
        delete_payload = [{"id": oid} for oid in created_ids]
        await _run(
            live_client,
            live_schema,
            "extras",
            "tags",
            "bulk-delete",
            body=delete_payload,
        )


# ---------------------------------------------------------------------------
# 6. Auto-pagination (list_all_pages)
# ---------------------------------------------------------------------------


async def test_live_auto_pagination(live_client: NetBoxApiClient, live_schema) -> None:
    """list_all_pages follows next-links and returns a synthesised single-page response."""
    response = await list_all_pages(
        client=live_client,
        index=live_schema,
        group="extras",
        resource="tags",
        query_pairs=[],
        max_records=500,
    )
    data = json.loads(response.text)
    assert "results" in data
    assert isinstance(data["results"], list)
    # count should equal the length of results when all pages are fetched
    assert data.get("count") == len(data["results"])


# ---------------------------------------------------------------------------
# 7. CLI-level live test (demo dynamic command)
# ---------------------------------------------------------------------------


def test_live_cli_list_tags(demo_cfg: Config) -> None:
    """nbx demo extras tags list — end-to-end CLI path with real credentials."""
    runner = CliRunner()

    def _fake_ensure_demo() -> Config:
        return demo_cfg

    # Patch the module-level name that demo_callback looks up at call time
    original = cli_demo._ensure_demo_runtime_config
    cli_demo._ensure_demo_runtime_config = _fake_ensure_demo
    try:
        result = runner.invoke(cli.app, ["demo", "extras", "tags", "list", "--json"])
    finally:
        cli_demo._ensure_demo_runtime_config = original

    assert result.exit_code == 0, (
        f"CLI exited with {result.exit_code}.\nOutput:\n{result.stdout}"
        + (f"\nException:\n{result.exception}" if result.exception else "")
    )
    # CLI prepends "Status: NNN\n" before the JSON body — strip it
    json_start = result.stdout.find("{")
    assert json_start != -1, f"No JSON object found in output:\n{result.stdout}"
    body = json.loads(result.stdout[json_start:])
    assert "count" in body or "results" in body


def test_live_cli_filters_tags(demo_cfg: Config) -> None:
    """nbx demo extras tags filters — filter discovery via CLI (local schema, no HTTP)."""
    runner = CliRunner()

    def _fake_ensure_demo() -> Config:
        return demo_cfg

    original = cli_demo._ensure_demo_runtime_config
    cli_demo._ensure_demo_runtime_config = _fake_ensure_demo
    try:
        result = runner.invoke(cli.app, ["demo", "extras", "tags", "filters"])
    finally:
        cli_demo._ensure_demo_runtime_config = original

    assert result.exit_code == 0, (
        f"CLI exited with {result.exit_code}.\nOutput:\n{result.stdout}"
        + (f"\nException:\n{result.exception}" if result.exception else "")
    )
    # Filters output must be non-empty
    assert result.stdout.strip(), "Expected filter parameter output"
