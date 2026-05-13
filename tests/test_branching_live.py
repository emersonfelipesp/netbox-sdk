"""Live-NetBox smoke tests for the ``netbox-branching`` plugin surface.

Auto-skips when no live NetBox is configured via the ``NETBOX_URL`` env var
(set by ``.github/workflows/test.yml`` in the live matrix), and again when
the running NetBox does not have the ``netbox-branching`` plugin installed.

The matrix entries that opt into branching coverage should provision the
plugin separately — until then this file is a no-op against the published
``netboxcommunity/netbox`` images, which is intentional.
"""

from __future__ import annotations

import os
import uuid

import pytest

from netbox_sdk import api
from netbox_sdk.branching import BranchingClient

pytestmark = pytest.mark.suite_sdk


def _skip_if_no_live_netbox() -> tuple[str, str]:
    url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not url or not token:
        pytest.skip("NETBOX_URL/NETBOX_TOKEN not set — live test skipped")
    return url, token


async def _client_or_skip() -> BranchingClient:
    url, token = _skip_if_no_live_netbox()
    nb = api(base_url=url, token=token, ssl_verify=False)
    branching = BranchingClient(nb)
    if not await branching.is_available():
        pytest.skip("netbox-branching plugin is not installed on the live NetBox")
    return branching


async def test_live_branching_feature_detection() -> None:
    branching = await _client_or_skip()
    # If we reached here, is_available() already returned True. A second
    # call must still succeed.
    assert await branching.is_available() is True


async def test_live_branching_create_list_delete_roundtrip() -> None:
    branching = await _client_or_skip()

    name = f"sdk-ci-{uuid.uuid4().hex[:6]}"
    created = await branching.create(name=name)
    schema_id = str(created.get("schema_id") or "")
    assert schema_id, "newly-created branch is missing schema_id"

    try:
        listed = await branching.list()
        assert any(str(b.get("schema_id") or "") == schema_id for b in listed), (
            f"branch {schema_id} not present in list response"
        )
    finally:
        await branching.delete(schema_id)
