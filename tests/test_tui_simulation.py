"""Regression coverage for the docgen-backed TUI simulation manifest."""

from __future__ import annotations

from pathlib import Path

import pytest

from netbox_cli import tui_simulation

pytestmark = pytest.mark.suite_tui


def test_tui_simulation_state_and_theme_lists_are_stable() -> None:
    assert tui_simulation.STATE_IDS == ("home", "devices", "details", "filter", "support")
    assert tui_simulation.THEMES == (
        "netbox-dark",
        "netbox-light",
        "dracula",
        "tokyo-night",
        "onedark-pro",
    )


def test_tui_simulation_filename_pattern_is_stable() -> None:
    assert (
        tui_simulation.simulation_filename("details", "tokyo-night")
        == "main-browser-details-tokyo-night.svg"
    )


def test_tui_simulation_manifest_shape_includes_hotspots() -> None:
    captures = {
        state_id: {
            theme: {
                "svg": tui_simulation.simulation_filename(state_id, theme),
                "hotspots": [
                    {
                        "id": "close-tui",
                        "label": "Close TUI",
                        "action": "close",
                        "widget_id": "close_tui_button",
                        "region": {"x": 1, "y": 2, "width": 3, "height": 4},
                    }
                ],
            }
            for theme in tui_simulation.THEMES
        }
        for state_id in tui_simulation.STATE_IDS
    }

    manifest = tui_simulation.build_manifest(
        captures=captures,
        generated_at="2026-05-05T00:00:00+00:00",
        source_commit="abc123",
        source_artifacts=[{"path": "docs/generated/raw/example.json", "exists": True}],
    )

    assert manifest["schema_version"] == 1
    assert manifest["command"] == "nbx tui"
    assert manifest["source_commit"] == "abc123"
    assert manifest["terminal_size"] == {"columns": 200, "rows": 60}
    assert manifest["state_ids"] == list(tui_simulation.STATE_IDS)
    assert manifest["themes"] == list(tui_simulation.THEMES)
    assert [state["id"] for state in manifest["states"]] == list(tui_simulation.STATE_IDS)
    first_capture = manifest["states"][0]["captures"]["netbox-dark"]
    assert first_capture["svg"] == "main-browser-home-netbox-dark.svg"
    assert first_capture["hotspots"][0]["region"] == {"x": 1, "y": 2, "width": 3, "height": 4}


def test_tui_simulation_default_paths_live_under_docs_generated() -> None:
    output, assets = tui_simulation.resolve_tui_simulation_paths(None, None)
    repo_root = Path(tui_simulation.__file__).resolve().parent.parent

    assert output == repo_root / "docs" / "generated" / "tui-simulation" / "main-browser.json"
    assert assets == output.parent
