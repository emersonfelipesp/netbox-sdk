"""Django Model TUI basic tests.

Basic tests to ensure the Django Model TUI can be instantiated and contains
the expected VerticalScroll containers for scrollbar functionality.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Static

from netbox_cli.ui.django_model_app import DjangoModelTuiApp


@pytest.fixture()
def mock_model_store():
    """Mock Django model store with minimal data."""
    store = MagicMock()
    store.exists.return_value = True
    store.load.return_value = {
        "models": {},
        "edges": [],
        "stats": {"total_models": 0, "total_edges": 0, "apps": []},
        "meta": {"source_path": "/fake/netbox", "total_models": 0},
    }
    store.get_model_source.return_value = "# Empty model"
    return store


@pytest.mark.asyncio
async def test_django_model_tui_can_be_instantiated(mock_model_store):
    """Test that the Django Model TUI can be created without errors."""
    app = DjangoModelTuiApp(store=mock_model_store)
    assert app is not None
    assert app.store == mock_model_store


@pytest.mark.asyncio
async def test_main_content_tabs_use_vertical_scroll_containers(mock_model_store):
    """Test that main content tabs are wrapped in VerticalScroll containers."""
    app = DjangoModelTuiApp(store=mock_model_store)

    async with app.run_test(size=(160, 50)) as pilot:
        await pilot.pause()

        # Check that each main content Static widget is inside a VerticalScroll container
        diagram_widget = app.query_one("#dm_diagram", Static)
        source_widget = app.query_one("#dm_source_code", Static)
        fields_widget = app.query_one("#dm_fields", Static)
        stats_widget = app.query_one("#dm_stats", Static)

        # Check that their parent containers are VerticalScroll widgets
        assert isinstance(diagram_widget.parent, VerticalScroll)
        assert isinstance(source_widget.parent, VerticalScroll)
        assert isinstance(fields_widget.parent, VerticalScroll)
        assert isinstance(stats_widget.parent, VerticalScroll)


@pytest.mark.asyncio
async def test_django_model_tui_renders_basic_content(mock_model_store):
    """Test that the Django Model TUI renders with expected initial content."""
    app = DjangoModelTuiApp(store=mock_model_store)

    async with app.run_test(size=(80, 25)) as pilot:
        await pilot.pause()

        # Should have the main content widgets
        diagram_widget = app.query_one("#dm_diagram", Static)
        source_widget = app.query_one("#dm_source_code", Static)

        # Should have initial placeholder content
        assert "Select a model" in str(diagram_widget.content)
        assert "Select a model" in str(source_widget.content)
