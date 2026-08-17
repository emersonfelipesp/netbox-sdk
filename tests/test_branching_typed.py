"""Tests for typed-client branching wiring across all supported versions.

For **every registered** NetBox release line the typed client must expose
``plugins.branching`` so callers using the typed API surface can reach the
netbox-branching plugin without falling back to the raw client. v4.4 wires the
full typed PluginsBranchingApp built on the bundled endpoint classes; every other
line uses the dict-based RawBranchingApp from typed_runtime.

The parametrization is derived from ``SUPPORTED_NETBOX_VERSIONS`` rather than
transcribed. A hardcoded list silently skips a newly registered line — which is
how NetBox 4.7 shipped without branching coverage.
"""

from __future__ import annotations

import pytest

from netbox_sdk.typed_api import typed_api
from netbox_sdk.typed_runtime import RawBranchingApp
from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS

pytestmark = pytest.mark.suite_sdk


TYPED_BRANCHING_LINE = "4.4"
RAW_BRANCHING_LINES = tuple(
    line for line in SUPPORTED_NETBOX_VERSIONS if line != TYPED_BRANCHING_LINE
)


@pytest.mark.parametrize("version", SUPPORTED_NETBOX_VERSIONS)
def test_typed_plugins_branching_accessor_exists(version: str) -> None:
    api = typed_api("http://example", token="t", netbox_version=version)
    branching = api.plugins.branching
    assert branching is not None


@pytest.mark.parametrize("version", RAW_BRANCHING_LINES)
def test_typed_branching_is_raw_for_non_v44(version: str) -> None:
    api = typed_api("http://example", token="t", netbox_version=version)
    assert isinstance(api.plugins.branching, RawBranchingApp)


def test_typed_branching_for_v44_exposes_branches_endpoint() -> None:
    api = typed_api("http://example", token="t", netbox_version=TYPED_BRANCHING_LINE)
    branching = api.plugins.branching
    # v4.4 ships the fully typed wrapper — it should have a typed
    # ``branches`` accessor rather than the dict-based methods.
    assert hasattr(branching, "branches")
