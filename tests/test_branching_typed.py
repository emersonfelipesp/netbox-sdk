"""Tests for typed-client branching wiring across all supported versions.

For every supported NetBox release line (4.3, 4.4, 4.5, 4.6) the typed
client must expose ``plugins.branching`` so callers using the typed API
surface can reach the netbox-branching plugin without falling back to the
raw client. v4.4 wires the full typed PluginsBranchingApp built on the
bundled endpoint classes; v4.3/v4.5/v4.6 use the dict-based
RawBranchingApp from typed_runtime.
"""

from __future__ import annotations

import pytest

from netbox_sdk.typed_api import typed_api
from netbox_sdk.typed_runtime import RawBranchingApp

pytestmark = pytest.mark.suite_sdk


@pytest.mark.parametrize("version", ["4.3", "4.4", "4.5", "4.6"])
def test_typed_plugins_branching_accessor_exists(version: str) -> None:
    api = typed_api("http://example", token="t", netbox_version=version)
    branching = api.plugins.branching
    assert branching is not None


@pytest.mark.parametrize("version", ["4.3", "4.5", "4.6"])
def test_typed_branching_is_raw_for_non_v44(version: str) -> None:
    api = typed_api("http://example", token="t", netbox_version=version)
    assert isinstance(api.plugins.branching, RawBranchingApp)


def test_typed_branching_for_v44_exposes_branches_endpoint() -> None:
    api = typed_api("http://example", token="t", netbox_version="4.4")
    branching = api.plugins.branching
    # v4.4 ships the fully typed wrapper — it should have a typed
    # ``branches`` accessor rather than the dict-based methods.
    assert hasattr(branching, "branches")
