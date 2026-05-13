"""Tests for the TUI branching surface.

Covers the persistent-header mechanism, ``BranchPill`` visual states, and
``TuiState`` round-tripping of the active branch fields. The full Pilot
flow for the modal switcher is exercised lazily via a constructed
``BranchSwitcherScreen`` instance — the goal is to catch wiring
regressions without requiring a live NetBox or a full Textual app stack.
"""

from __future__ import annotations

import pytest

from netbox_sdk.client import NetBoxApiClient
from netbox_sdk.config import Config
from netbox_tui.branch_screen import (
    BRANCH_HEADER,
    BranchPill,
    BranchSwitcherScreen,
    apply_branch_to_client,
)
from netbox_tui.state import TuiState

pytestmark = pytest.mark.suite_tui


def _make_client() -> NetBoxApiClient:
    cfg = Config(base_url="http://example", token="t", ssl_verify=False)
    return NetBoxApiClient(cfg)


def test_apply_branch_to_client_sets_and_clears_header() -> None:
    client = _make_client()
    assert BRANCH_HEADER not in client.persistent_headers

    apply_branch_to_client(client, "td5smq0f")
    assert client.persistent_headers[BRANCH_HEADER] == "td5smq0f"

    apply_branch_to_client(client, None)
    assert BRANCH_HEADER not in client.persistent_headers


def test_persistent_headers_are_merged_into_request_headers() -> None:
    """The client must include persistent headers on every request — even
    when called from a fresh asyncio task that has its own ContextVar copy.
    We verify this at the attribute level by reading the dict directly.
    """
    client = _make_client()
    apply_branch_to_client(client, "abc12345")
    assert client.persistent_headers == {BRANCH_HEADER: "abc12345"}


def test_branch_pill_set_branch_toggles_active_class() -> None:
    pill = BranchPill()
    pill.set_branch("td5smq0f", "my-branch")
    assert "-active" in pill.classes

    pill.set_branch(None, None)
    assert "-active" not in pill.classes


def test_branch_pill_set_available_toggles_hidden_class() -> None:
    pill = BranchPill(classes="-hidden")
    pill.set_available(True)
    assert "-hidden" not in pill.classes

    pill.set_available(False)
    assert "-hidden" in pill.classes


def test_tui_state_round_trips_active_branch_fields(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("netbox_sdk.config.config_path", lambda: tmp_path / "config.json")
    from netbox_tui import state as state_mod

    saved = TuiState(active_branch_schema_id="td5smq0f", active_branch_name="my-branch")
    state_mod.save_tui_state(saved, "http://example")
    loaded = state_mod.load_tui_state("http://example")

    assert loaded.active_branch_schema_id == "td5smq0f"
    assert loaded.active_branch_name == "my-branch"


def test_tui_state_defaults_active_branch_to_none() -> None:
    state = TuiState()
    assert state.active_branch_schema_id is None
    assert state.active_branch_name is None


def test_branch_switcher_screen_can_be_constructed_with_branches() -> None:
    branches = [
        {"schema_id": "abc12345", "name": "feature-x", "status": {"value": "ready"}},
        {"schema_id": "def67890", "name": "feature-y", "status": "ready"},
    ]
    screen = BranchSwitcherScreen(branches=branches, active_schema_id="abc12345")
    # Internal state should preserve the input list and active marker.
    assert screen._branches == branches
    assert screen._active == "abc12345"
