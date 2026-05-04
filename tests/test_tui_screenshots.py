"""Regression coverage for the automated TUI screenshot harness."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from netbox_tui.graphql_app import NetBoxGraphqlTuiApp
from scripts import tui_screenshots

pytestmark = pytest.mark.suite_tui


def test_screenshot_harness_registers_graphql_tui() -> None:
    app_ids = [app_id for app_id, _, _ in tui_screenshots.TUIS]
    assert "graphql" in app_ids


def test_graphql_screenshot_kwargs_use_dedicated_app_and_theme() -> None:
    base_client = MagicMock()
    base_client.config = MagicMock(base_url="https://demo.netbox.dev")

    kwargs = tui_screenshots.get_app_kwargs(
        app_id="graphql",
        theme="dracula",
        index=MagicMock(),
        client=base_client,
    )

    app = NetBoxGraphqlTuiApp(**kwargs)

    assert isinstance(app, NetBoxGraphqlTuiApp)
    assert app.theme_name == "dracula"
    assert kwargs["client"].config is base_client.config


def test_graphql_screenshot_state_patch_seeds_query_history() -> None:
    patches = tui_screenshots.screenshot_state_patches("graphql")

    assert len(patches) == 2


def test_graphql_screenshot_filename_pattern_is_stable() -> None:
    filename = "tui-graphql-tokyo-night.svg"
    assert filename.startswith("tui-graphql-")
    assert filename.endswith(".svg")
