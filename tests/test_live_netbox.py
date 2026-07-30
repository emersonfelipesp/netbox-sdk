"""Read-only compatibility checks against the live NetBox CI matrix."""

from __future__ import annotations

import os

import pytest

from netbox_sdk import api, typed_api

pytestmark = [pytest.mark.suite_sdk, pytest.mark.live]


def _live_connection() -> tuple[str, str]:
    url = os.getenv("NETBOX_URL")
    token = os.getenv("NETBOX_TOKEN")
    if not url or not token:
        pytest.skip("NETBOX_URL/NETBOX_TOKEN not set — live test skipped")
    return url, token


async def test_live_core_status_schema_and_typed_list() -> None:
    """Exercise the same read-only SDK path on every supported CI matrix entry."""

    url, token = _live_connection()
    live_api = api(url, token=token)

    status = await live_api.status()
    version = str(status["netbox-version"])
    release_line = ".".join(version.split(".")[:2])
    assert release_line in {"4.5", "4.6"}

    schema = await live_api.openapi()
    assert str(schema["info"]["version"]).startswith(release_line)
    assert "/api/dcim/devices/" in schema["paths"]

    typed = typed_api(url, token=token, netbox_version=release_line)
    page = await typed.dcim.devices.list({"limit": 1})
    assert isinstance(page.results, list)


async def test_live_v466_any_tag_filters() -> None:
    """Verify the tag filter aliases added to the NetBox v4.6.6 schema."""

    url, token = _live_connection()
    live_api = api(url, token=token)
    version = str((await live_api.status())["netbox-version"])
    if version != "4.6.6":
        pytest.skip("tag__any and tag_id__any are a NetBox v4.6.6 regression target")

    typed = typed_api(url, token=token, netbox_version="4.6")
    by_slug = await typed.dcim.devices.list(
        {"limit": 1, "tag__any": ["sdk-ci-tag-that-does-not-exist"]}
    )
    by_id = await typed.dcim.devices.list({"limit": 1, "tag_id__any": [2147483647]})

    assert by_slug.results == []
    assert by_id.results == []
