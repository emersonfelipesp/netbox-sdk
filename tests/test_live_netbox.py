"""Compatibility checks against ephemeral NetBox CI matrix instances."""

from __future__ import annotations

import os
from contextlib import AsyncExitStack
from uuid import uuid4

import pytest

from netbox_sdk import api, typed_api
from scripts.check_live_netbox_status import live_status_matches

pytestmark = [pytest.mark.suite_sdk, pytest.mark.live]


def _live_connection() -> tuple[str, str]:
    url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not url or not token:
        pytest.skip("NETBOX_URL/NETBOX_TOKEN not set — live test skipped")
    return url, token


def _require_ephemeral_mutation_opt_in() -> None:
    if os.getenv("NETBOX_LIVE_TEST") != "1":
        pytest.skip("mutating live fixtures require NETBOX_LIVE_TEST=1")


async def test_live_core_status_schema_and_typed_list() -> None:
    """Exercise the same read-only SDK path on every supported CI matrix entry."""

    url, token = _live_connection()
    async with AsyncExitStack() as cleanup:
        live_api = api(url, token=token)
        cleanup.push_async_callback(live_api.client.close)
        status = await live_api.status()
        version = str(status["netbox-version"])
        expected = os.getenv("NETBOX_EXPECTED_VERSION")
        if expected:
            want = expected.removeprefix("v")
            assert live_status_matches(expected, version), (
                f"live job expected NetBox {want}; /api/status/ reported {version}"
            )
        release_line = ".".join(version.split(".")[:2])
        assert release_line in {"4.5", "4.6", "4.7"}

        schema = await live_api.openapi()
        assert str(schema["info"]["version"]).startswith(release_line)
        assert "/api/dcim/devices/" in schema["paths"]
        if release_line == "4.7":
            assert "/api/dcim/cooling-sources/" in schema["paths"]

        typed = typed_api(url, token=token, netbox_version=release_line)
        cleanup.push_async_callback(typed.client.close)
        page = await typed.dcim.devices.list({"limit": 1})
        assert isinstance(page.results, list)


async def test_live_v466_any_tag_filters() -> None:
    """Verify repeated any-tag filters using disposable v4.6.6 fixtures."""

    url, token = _live_connection()
    _require_ephemeral_mutation_opt_in()
    async with AsyncExitStack() as cleanup:
        live_api = api(url, token=token)
        cleanup.push_async_callback(live_api.client.close)
        version = str((await live_api.status())["netbox-version"])
        if version != "4.6.6":
            pytest.skip("tag__any and tag_id__any are a NetBox v4.6.6 regression target")

        typed = typed_api(url, token=token, netbox_version="4.6")
        cleanup.push_async_callback(typed.client.close)
        fixture = uuid4().hex
        tag_a = await live_api.extras.tags.create(
            name=f"SDK CI any A {fixture}", slug=f"sdk-ci-any-a-{fixture}"
        )
        cleanup.push_async_callback(tag_a.delete)
        tag_b = await live_api.extras.tags.create(
            name=f"SDK CI any B {fixture}", slug=f"sdk-ci-any-b-{fixture}"
        )
        cleanup.push_async_callback(tag_b.delete)
        site = await live_api.dcim.sites.create(
            name=f"SDK CI any site {fixture}",
            slug=f"sdk-ci-any-site-{fixture}",
            tags=[tag_a.id],
        )
        cleanup.push_async_callback(site.delete)

        by_slug = await typed.dcim.sites.list({"limit": 10, "tag__any": [tag_a.slug, tag_b.slug]})
        by_id = await typed.dcim.sites.list({"limit": 10, "tag_id__any": [tag_a.id, tag_b.id]})

        assert site.id in {item.id for item in by_slug.results}
        assert site.id in {item.id for item in by_id.results}
